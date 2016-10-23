import enum

from .base import Player
from .map import Map
from .tile import GameTile


class GameState(object):
    def __init__(self):
        self.player0, self.player1 = Player(0), Player(1)
        self.map = self.init_map()
        self.turn_count = 1

    def init_map(self):
        assert not hasattr(self, 'map') or self.map is None
        self.map = Map(p0=self.player0, p1=self.player1)

    def state_for_player(self, player):
        raise NotImplementedError

    def orders_from_player(self, orders):
        raise NotImplementedError

    def evaluate_turn(self):
        '''execute planned actions for one turn'''
        # NOTE: chase 2nd would allow multi-action to attack & move in single pass
        for step in ('attack', 'move', 'chase'):
            # NOTE: execution order by-tile, all actions need to be synced, otherwise can be unfair
            for unit in self.map.get_all_units():
                unit.end_of_turn(step)
        self.turn_count += 1