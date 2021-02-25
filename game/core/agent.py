import pygame
from .constants import WINDOW_WIDTH, WINDOW_HEIGHT
from ..board_utils.board import Board


class Agent:
    def __init__(self, i: int, j: int,  screen: any, board: Board):
        # index of where the agent is 
        self._i = 0
        self._j = 0

        self._screen = screen    
        self._board = board

        # tile width is passed in so we know how large to make the agent
        self._tile_width = board.tile_width

    """
    BEGIN AI SPECIFIC FUNCTIONS

    The AI should ONLY be interacting with the following functions
    """

    def move_up(self):
        # Make sure we don't go off screen
        self._j = max(0, self._j - 1)

    def move_down(self):
        # Make sure we don't go off screen
        self._j = min(self._board.dim-1, self._j + 1)
    
    def move_left(self):
        # Make sure we don't go off screen
        self._i = max(0, self._i - 1)

    def move_right(self):
        # Make sure we don't go off screen
        self._i = min(self._board.dim-1, self._i+1)    

    def open_tile(self):
        # interact with current tile and change its state
        self._board.open_tile(self._j, self._i)

    """
    END AI SPECIFIC FUNCTIONS
    """

    @property
    def i(self):
        """
        Returns i index of where the agent is in the board    
        """
        return self._i

    @property
    def j(self):
        """
        Returns j index of where the agent is in the board
        """
        return self._j

    @property
    def screen(self):
        """
        Return pygame screen instance
        """
        return self._screen

    def draw(self):
        """
        Returns pygame rect to draw on the screen
        """
        # Agent is 80% the size of a tile
        agent_width = self._tile_width * 0.8
        # Create agent rectangle (can use sprites later)
        rect = pygame.Rect(self._i * self._tile_width, self._j * self._tile_width, agent_width, agent_width)
        # Center (inplace) the agent rectangle
        rect.move_ip(self._tile_width * 0.1, self._tile_width * .1)
        # Draw the agent
        pygame.draw.rect(self._screen, 'orange', rect, 5)
