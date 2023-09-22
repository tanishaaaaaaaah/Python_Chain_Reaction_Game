from abc import ABC, abstractmethod

import pygame
import pygame.font as font
import pygame.gfxdraw as gfxdraw

import chain_reaction.graphics.sprites as sprites
import chain_reaction.wrappers.engine as engine


# ----------- COLORS -------------
COL_BACK = (0, 0, 0)
COL_FORE = (255, 255, 255)
COL_PLR1 = (250, 100, 40)
COL_PLR2 = (40, 200, 100)


# --------- DIMS -----------
R_THIC = 10
R_VOFF = 40
G_HOFF = 50
G_VOFF = 70
G_WIDC = 50
G_WALL = 2


# -------- ON INIT ----------
G_SHAP = None
G_DIMS = None
R_DIMS = None
W_DIMS = None

ORB_PL1 = None
ORB_PL2 = None


# ----------- INIT ---------------
def init(g_shape=(9, 6)):
    """
    Calculate dimensions and construct sprites
    Input : g_shape (rows, cols)
    """
    global G_SHAP, G_DIMS, R_DIMS, W_DIMS
    global ORB_PL1, ORB_PL2

    # pygame modules
    font.init()

    # calculate dims
    G_SHAP = (g_shape[1], g_shape[0])
    G_DIMS = (G_SHAP[0] * G_WIDC + G_WALL, G_SHAP[1] * G_WIDC + G_WALL)
    R_DIMS = (G_DIMS[0], R_THIC)
    W_DIMS = (G_DIMS[0] + (2 * G_HOFF), G_DIMS[1] + G_HOFF + G_VOFF)

    # construct sprites
    ORB_SIZ = G_WIDC - G_WALL
    ORB_PL1 = sprites.construct_orbs(COL_PLR1, COL_BACK, ORB_SIZ)
    ORB_PL2 = sprites.construct_orbs(COL_PLR2, COL_BACK, ORB_SIZ)


# ---------- CLASSES -------------
class BaseGameWindow(ABC):
    def __init__(self, fps):
        """ Most Basic Game Window """

        # window pointers
        self.surface = pygame.display.set_mode(W_DIMS)
        self.clock = pygame.time.Clock()
        self.fps = fps

        # status
        self.locked = False
        self.open = True

        # mouse click and index
        self.mclk = False
        self.midx = None

    def clear(self):
        self.surface.fill(COL_BACK)

    def update(self):
        pygame.display.update()

    def event_flush(self):
        pygame.event.clear()

    def event_handler(self):
        """ Handle events in window """
        # Refresh values
        self.mclk = False
        self.midx = None

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.open = False
                return

            elif event.type == pygame.MOUSEBUTTONUP:
                # if locked, do nothing
                if self.locked:
                    continue

                self.mclk = True
                crx, cry = pygame.mouse.get_pos()
                idx = ((cry - G_VOFF) // G_WIDC, (crx - G_HOFF) // G_WIDC)
                val = (0 <= idx[0] < G_SHAP[1]) * (0 <= idx[1] < G_SHAP[0])
                self.midx = idx if val else None

    def draw_indicator(self, player):
        """ Draw rectangle to indicate next player """
        pcolor = COL_PLR2 if player else COL_PLR1
        nxrect = (G_HOFF, R_VOFF, G_DIMS[0], R_THIC)
        pygame.draw.rect(self.surface, pcolor, nxrect)

    def draw_grid(self):
        """ Draw grid on screen """
        gwid, ghgt = G_DIMS

        # horizontal lines
        for j in range(G_SHAP[1] + 1):
            grect = (G_HOFF, G_VOFF + j * G_WIDC, gwid, G_WALL)
            pygame.draw.rect(self.surface, COL_FORE, grect)

        # vertical lines
        for i in range(G_SHAP[0] + 1):
            grect = (G_HOFF + i * G_WIDC, G_VOFF, G_WALL, ghgt)
            pygame.draw.rect(self.surface, COL_FORE, grect)

    def draw_orbs(self, board, ignore=[]):
        """ Draw orb sprites on the surface """
        gcol, grow = G_SHAP
        offx, offy = (G_HOFF + G_WALL, G_VOFF + G_WALL)

        for idx in range(grow * gcol):
            # ignore index
            if idx in ignore:
                continue

            # blit appropriate sprite on surface
            ccount = board[idx]
            if ccount != 0:
                i_y, i_x = idx // gcol, idx % gcol
                pos = (G_WIDC * i_x + offx, G_WIDC * i_y + offy)
                psprite = ORB_PL1 if ccount > 0 else ORB_PL2
                self.surface.blit(psprite[abs(ccount) - 1], pos)

    def draw_all(self, board, player):
        """ Draw all drawable elements """
        self.clear()
        self.draw_grid()
        self.draw_indicator(player)
        self.draw_orbs(board)
        self.update()

    @abstractmethod
    def on_game_start(self):
        """ Splash Screen Callback """
        return

    @abstractmethod
    def on_game_move(self, game, move):
        """ Game Piece Move Callback """
        return

    @abstractmethod
    def on_game_end(self, game):
        """ Game Over Callback """
        return


class StaticGameWindow(BaseGameWindow):
    def __init__(self, fps):
        """
        Display static graphics
        Very light on resources
        """
        super().__init__(fps)

    def on_game_start(self):
        """ Splash Screen Callback """
        return

    def on_game_move(self, game: engine.ChainReactionGame, move):
        """ Game Piece Move Callback """

        #  draw if no move specified
        if move is None:
            self.draw_all(game.board, game.player)
            return

        # play
        game.make_move(move)
        self.draw_all(game.board, game.player)

    def on_game_end(self, game):
        """ Game Over Callback """

        if game.winner == 0:
            print("Red Wins!")
        elif game.winner == 1:
            print("Green Wins!")
        elif game.winner == 2:
            print("")

        # quit pygame
        pygame.quit()


class AnimatedGameWindow(BaseGameWindow):
    def __init__(self, fps, flight_steps=10):
        """
        Window that displays animations
        -------------------------------
        - fps          - frame rate limit
        - flight_steps - steps in a flight animation
        """

        super().__init__(fps)

        self.flight_steps = flight_steps

    def draw_flights(self, flights, progress, player):
        # setup
        gcol, grow = G_SHAP
        offx, offy = (G_HOFF + G_WALL, G_VOFF + G_WALL)
        pcolor = COL_PLR2 if player else COL_PLR1
        prog_frac = progress / self.flight_steps

        for origin, dest in flights:

            # indices
            orig_posx = G_WIDC * (origin % gcol) + offx + G_WIDC // 2
            orig_posy = G_WIDC * (origin // gcol) + offy + G_WIDC // 2
            dest_posx = G_WIDC * (dest % gcol) + offx + G_WIDC // 2
            dest_posy = G_WIDC * (dest // gcol) + offy + G_WIDC // 2

            # calculate positions
            pos_x = int(orig_posx + prog_frac * (dest_posx - orig_posx))
            pos_y = int(orig_posy + prog_frac * (dest_posy - orig_posy))

            # draw in present position
            gfxdraw.aacircle(self.surface, pos_x, pos_y, 10, pcolor)
            gfxdraw.filled_circle(self.surface, pos_x, pos_y, 10, pcolor)

    def explode_orbs(self, board, explosions, player, callback=None):
        """
        Show orb explosion animation
        Does not return until animation is over
        Internal event handling
        """

        # immediate return if explosions are absent
        if not explosions:
            return

        # set up origin and final indices for flight
        flights = [
            (origin, dest)
            for origin in explosions
            for dest in engine.NTABLE[origin]
        ]

        # uniform speed
        for progress in range(self.flight_steps):
            self.clear()
            self.draw_grid()
            self.draw_indicator(player)
            self.draw_orbs(board, ignore=explosions)
            self.draw_flights(flights, progress, player)
            callback() if callback else None  # optional callback
            self.update()
            self.event_handler()
            self.clock.tick(self.fps)

    def on_game_start(self):
        """ Splash Screen """
        return

    def on_game_move(self, game: engine.ChainReactionAnimated, move):
        """ Function to execute when move specified """

        # draw if no move specified
        if move is None:
            self.draw_all(game.board, game.player)
            return

        # invalid move
        if not game.make_move(move):
            return

        # lock to not respond to mouse clicks
        self.locked = True
        player = game.player

        # get steps until stable or game over
        while game.pending_moves and not game.game_over and self.open:

            # get board and explosions for animation
            prev_board, explosions = game.get_next_step()

            # draw explosions
            self.explode_orbs(prev_board, explosions, player)
            self.draw_all(game.board, game.player)

        # unlock window after handling events
        self.event_handler()
        self.locked = False

    def on_game_end(self, game: engine.ChainReactionAnimated):
        """ Game over screen """

        global ORB_PL1, ORB_PL2
        global COL_PLR1, COL_PLR2
        global COL_FORE

        # convert colors to grayscale
        COL_PLR1 = (30, 30, 30)
        COL_PLR2 = (30, 30, 30)
        COL_FORE = (30, 30, 30)
        ORB_PL1 = [sprites.grayscale(x, 0.2) for x in ORB_PL1]
        ORB_PL2 = [sprites.grayscale(x, 0.2) for x in ORB_PL2]

        # save player
        player = game.player
        self.flight_steps = 20  # slow-mo

        # construct game over text
        font_instance = font.SysFont("Ubuntu Mono", 50, True, False)
        message = "GREEN WINS!" if game.winner else "RED WINS!"
        mscolor = (100, 255, 50) if game.winner else (255, 100, 50)
        game_over_text = font_instance.render(message, True, mscolor)
        text_w, text_h = game_over_text.get_size()
        text_dest = ((W_DIMS[0] - text_w) // 2, (W_DIMS[1] - text_h) // 2)
        blit_text = lambda: self.surface.blit(game_over_text, text_dest)

        # keep exploding for cool end-graphics
        while self.open and game.pending_moves:
            prev_board, explosions = game.get_next_step()

            self.explode_orbs(prev_board, explosions, player, blit_text)
            self.clear()
            self.draw_grid()
            self.draw_indicator(game.player)
            self.draw_orbs(game.board)
            blit_text()
            self.update()

        # draw static if pending moves are over
        if not game.pending_moves:
            self.clear()
            self.draw_grid()
            self.draw_indicator(game.player)
            self.draw_orbs(game.board)
            blit_text()
            self.update()
            while self.open:
                self.event_handler()
                self.clock.tick(self.fps)

        # voluntary close
        if not game.game_over and not self.open:
            print("")

        font.quit()
        pygame.quit()
