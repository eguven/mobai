import enum

from .base import Player
from .map import Map
from .tile import GameTile


class ActionType(enum.Enum):
    clear = 0
    target = 1


class Action(object):
    def __init__(self, player, unit, _type, target=None):
        assert player == unit.player
        assert _type in ActionType.__members__
        self.player = player
        self.unit = unit
        self.action_type = ActionType[_type]
        self.target = target
        if self.action_type is ActionType.target:
            assert target is not None
            if isinstance(target, GameTile):
                assert unit.mobile


class GameState(object):
    '''
        * creating a GameState object initializes a game with map, players,
        tiles and buildings
        * `begin_turn` runs through the steps necessary prior to sending
        players the game state (eg. spawning units if necessary)
        * State representation are sent to players and actions are retrieved
        * Actions are verified and applied to units
        * `evaluate_turn` runs through the steps of executing actions and finishes turn
    '''
    def __init__(self):
        self.player0, self.player1 = Player(0), Player(1)
        self.map = self.init_map()
        self.turn = 0
        self.spawn_interval = 10

    def init_map(self):
        assert not hasattr(self, 'map') or self.map is None
        self.map = Map(p0=self.player0, p1=self.player1)

    def begin_turn(self):
        if self.turn % self.spawn_interval:
            self._spawn_new_units()

    def state_for_player(self, player):
        return dict(
            player_id=player.id, turn=self.turn,
            map=self.map.to_array(by_player=player),
        )

    def orders_from_player(self, orders):
        raise NotImplementedError

    def _spawn_new_units(self):
        for fort in self.map.get_forts():
            fort.spawn_soldiers(count=3)

    def _remove_dead_units(self):
        '''remove dead units and clear targets on them'''
        # TODO: might use for feedback
        dead_units = []
        for tile in self.map.tiles():
            dead_units.extend([unit for unit in tile.occupants if unit.health <= 0])
            tile.occupants = [unit for unit in tile.occupants if unit.health > 0]
        for unit in self.map.get_all_units():
            if unit.target in dead_units:
                unit.clear_target()

    def evaluate_turn(self):
        '''execute planned actions for one turn'''
        for step in ('attack', 'move', 'chase'):
            # NOTE: execution order by-tile, all actions need to be synced, otherwise can be unfair
            for unit in self.map.get_all_units():
                unit.end_of_turn(step)
        self._remove_dead_units()
        self.turn += 1
