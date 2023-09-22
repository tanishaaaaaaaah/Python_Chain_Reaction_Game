import random


# ---------- ON INIT ---------------
load_scores = None


# ----------- INIT -----------------
def init(backend: str):

    global load_scores

    # setting up c engine
    if backend == "c":
        import chain_reaction.backends.c_ext.minimax_agent as cagent

        load_scores = cagent.load_scores

    # setting up python engine
    else:
        import chain_reaction.backends.python.minimax_agent as pagent

        load_scores = pagent.load_scores


# ------- WRAPPER FUNCTIONS --------
def best_move(board: list, player: int, depth: int, randn: int) -> int:
    """
    Get weighted random choice of best n moves
    If there is an immediate winning move, always return it
    """

    # make a list of (move, score)
    score_list = load_scores(board, player, depth)
    heatmap = list(enumerate(score_list))

    # get random move with decreasing weights
    heatmap.sort(key=lambda x: x[1], reverse=True)
    m_moves = [i[0] for i in heatmap if i[1] > 0][:randn]
    weights = [6, 4, 2, 1, 1][: len(m_moves)]

    # if there is a winning move or no random choice return
    # return random choice if more than one score is positive
    if heatmap[0][1] == 10000 or len(m_moves) <= 1:
        return heatmap[0][0]
    else:
        return random.choices(m_moves, weights)[0]
