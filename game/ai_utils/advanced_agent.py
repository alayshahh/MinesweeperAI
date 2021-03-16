import pygame
import numpy as np
from sympy import Symbol, linsolve, linear_eq_to_matrix, solveset, FiniteSet, Eq, S, symbols, simplify, solve, And, satisfiable, Or
from ..core.constants import GAME_STATE, EVENT_MOVE_UP, EVENT_MOVE_DOWN, EVENT_MOVE_LEFT, EVENT_MOVE_RIGHT, EVENT_OPEN_TILE, TILES
from ..board_utils.board import Board
from ..core.agent import Agent
import time
import random
from ..board_utils.board_tile import BoardTile
from ..core.constants import TILES

"""
Types of Operations:
    - 
"""

"""
Knowledge Base:
    knowledge_base = {
        x: [(x+y+z, 1)],
        y: [(x+y+z, 1)],
        z: [(x+y+z, 1)]
    }
    keys are symbols, values are a list of tuples (lhs = sympy equation, rhs = integer)
"""


def start(board: Board, agent: Agent):
    """
    Start the advanced agent
    """

    # first tile we look at is the agent's starting position
    start_tile = board.get_tile(agent.i, agent.j)

    # is the agent finished traversing (i.e. no more moves left)
    agent_done = False

    # generate symbols

    # number of tiles flagged
    score = 0

    # stores safe tiles that we want to open (holds tile objects)
    tiles_to_open = [start_tile]  # start at the agent starting position

    # store visited tiles that we are not done with, tiles who still has unflagged/unopened neighbors (holds tile objects)
    unfinished_tiles = []

    while(not agent_done):
        time.sleep(0.01)
        pygame.event.post(pygame.event.Event(
            pygame.USEREVENT, attr1="force rerender"))

        if not tiles_to_open:  # if the list to open new tiles is empty, then we must choose a new tile to get more information
            # TODO inference method

            random_tile = random_tile_to_open(board)

            # ends the game, no tiles remaining to open
            if not random_tile:
                print("GAME OVER, SCORE = ", score)
                # pygame.event.post(pygame.event.Event(pygame.QUIT, attr1={"Score": score})) #THIS CLOSES THE SCREEN TOO FAST
                return score
            tiles_to_open.append(random_tile)

        curr_tile = tiles_to_open.pop(0)

        i, j = curr_tile.i, curr_tile.j

        # update agent position
        agent.set_pos(i, j)

        # if the tile is unopened, we know (besides the very first) that it is safe
        if curr_tile.is_opened == False:
            board.open_tile(i, j)
            # we have to reassign curr_tile since the status has changed
            curr_tile = agent.get_tile()

        # now, check if we accidentally opened a mine
        if curr_tile.type == TILES.MINE:
            continue

        score = check_neighbors(
            curr_tile, board, unfinished_tiles, tiles_to_open, score)

        # since we add elements back into the queue, we only want to iterate a specific amount of times
        for i in range(len(unfinished_tiles)):
            # we want to remove the top element from the queue
            tile = unfinished_tiles.pop(0)
            score = check_neighbors(
                tile, board, unfinished_tiles, tiles_to_open, score)


def inference(board: Board, unfinished_tiles):
    # initialize KB with all tiles as keys
    #knowledge_base = {tile : [] for tilelist in board.tiles for tile in tilelist}
    all_equations = []

    # look at each tile
    for tile in unfinished_tiles:
        # if the tile is not opened or is opened and a mine, we cant get any info
        if not tile.is_opened:
            continue
        if tile.type == TILES.MINE:
            continue

        neighbors = board.get_neighboring_tiles(tile.i, tile.j)
        unopened_neighbors = [
            tile for tile in neighbors if not tile.is_opened and not tile.is_flagged]
        # since we only call this method when we have no more information we can collect using
        # the basic agent, unopened_neighbors should never have a length of 0.
        # But, just in case we assert
        assert len(unopened_neighbors) != 0

        val = tile.type.value

        # create the equation for the tile and value
        eqn = unopened_neighbors[0].get_symbol
        for i in range(1, len(unopened_neighbors)):
            eqn = eqn + unopened_neighbors[i].get_symbol

        index = len(all_equations)
        all_equations.append([eqn, val])

        # KB maps each variable in the equation to every equation it is present in
        # for neighbors in unopened_neighbors:
        #     knowledge_base[neighbors.get_symbol].append(all_equations[index])

    # once we have a knowledge base, we want to see if we can infer anything using 2 equations instead of 1
    # to do this we can either loop through each eqaution in eqn list and see if we can infer anything from the equations or reduce them


def subset_reduction(all_equations: list): 
    '''
    Reduces redundancies in equations
    i.e.
    A+C+D+E = 2
    A+D = 1
    Then we can reduce A+C+D+E = 2 into C+E = 1
    '''
    for i in range(len(all_equations)):
        for j in range(i+1, len(all_equations)):
            eq1 = all_equations[i][0]
            eq2 = all_equations[j][0]
            set1 = eq1.free_symbols
            set2 = eq2.free_symbols
            if set1.issubset(set2):
                # eq2 is a superset of eq1 so we can reduce eq2
                all_equations[j][0] = eq2 - eq1
                all_equations[j][1] = all_equations[j][1] - \
                    all_equations[i][1]  # update value of equation

            elif set2.issubset(set1):
                # eq1-eq2
                all_equations[i][0] = eq1 - eq2
                all_equations[i][1] = all_equations[i][1] - all_equations[j][1]


def double_inference(all_equations: list):
    '''
    looks at 2 equations and if they share the some of the same variables, we may be able to infer more info
    eq1 = A+B+C+D =2
    eq2 = B+D+E= 1
    eq1-eq2 = A+C - E = 1, then we can infer that E=0, then we can also infer A+C=1, B+D = 1 (Using subset reduction)

    '''

    for i in range(len(all_equations)):
        for j in range(i+1, len(all_equations)):
            eq1 = all_equations[i][0]
            eq2 = all_equations[j][0]
            set1 = eq1.free_symbols
            set2 = eq2.free_symbols
            # if they dont share any of the same variables cant get any new info
            if set1.isdisjoint(set2):
                continue
            if all_equations[i][1] > all_equations[j][1]:
                derived_eq = eq1-eq2
                derived_val = all_equations[i][1] - all_equations[j][1]
            else:
                derived_eq = eq2 - eq1
                derived_val = all_equations[j][1] - all_equations[i][1]

            # TODO FIGURE OUT WHAT WE NEED TO DO AFTER WE SUBTRACT 2 EQS


def random_tile_to_open(board: Board) -> BoardTile:
    """
    Pick a random tile to restart at by looking at board and choosing which 
    """
    available_tiles = []
    for tilelist in board.tiles:
        for tile in tilelist:
            if not tile.is_opened and not tile.is_flagged:
                available_tiles.append(tile)
    if not available_tiles:
        return
    # print(len(available_tiles))
    print("OPENING RANDOM TILE")
    rand = random.randint(0, len(available_tiles)-1)
    random_tile = available_tiles[rand]

    return random_tile


def check_neighbors(curr_tile: BoardTile, board: Board, unfinished_tiles: list, tiles_to_open: list, score: int):
    """
    looks at all neighbors for the current tiles, if it satisfies requirements, 
    it will either flag the neighboring tiles or add them to the tiles_to_open list
    returns the score (if we flag tiles, we want to increment score)
    """
    i, j = curr_tile.i, curr_tile.j
    # go over all neighboring cells
    neighbors = board.get_neighboring_tiles(i, j)
    unopened_neighbors = [
        tile for tile in neighbors if not tile.is_opened and not tile.is_flagged]
    mine_flagged_neighbors = [tile for tile in neighbors if tile.is_flagged or (
        tile.is_opened and tile.type == TILES.MINE)]

    total_neighbors = len(neighbors)
    total_unopened_neighbors = len(unopened_neighbors)
    total_mine_flagged_neighbors = len(mine_flagged_neighbors)

    clue = curr_tile.type.value

    # if we found all mines that are neighbors then the rest of the unopened neighbors are safe
    if total_mine_flagged_neighbors == clue:
        for tile in unopened_neighbors:
            if tile not in tiles_to_open:
                tiles_to_open.append(tile)
    # if the number of unopened neighbors equals the clue minus already flagged then all neighbors are mines
    elif total_unopened_neighbors == clue - total_mine_flagged_neighbors:
        for tile in unopened_neighbors:
            if not tile.is_flagged:
                tile.toggle_flag()
                print("FLAGGED TILE")
                print(tile.i, tile.j)
                score += 1
                print("Score = ", score)
    elif total_unopened_neighbors != 0:  # if the current tile still has unopened tiles, then we are not done with it
        unfinished_tiles.append(curr_tile)
    return score
