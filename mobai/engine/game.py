import enum
import gzip
import pickle

from .base import Player
from .map import Map


class ActionType(enum.Enum):
    target = 0
    clear_target = 1
    stop = 2


class Command(object):
    '''a command received from a player
    {'id': '<uuid>', 'action': '<action-type>.name', 'target': '<uuid>' | {'posx': X, 'posy': Y} }
    '''
    def __init__(self, player, command):
        # id present and not empty
        assert command.get('id') and isinstance(command['id'], str)
        # action present and valid
        assert 'action' in command and command['action'] in ActionType.__members__
        if ActionType[command['action']] is ActionType.target:
            # target present and valid
            assert 'target' in command and command['target']
            assert isinstance(command['target'], (str, dict))
        self.id = command['id']
        self.action = ActionType[command['action']]
        if self.action is ActionType.target:
            self.target = command['target']
            if isinstance(self.target, dict):
                # position target valid
                assert 'posx' in self.target and 'posy' in self.target
                assert isinstance(self.target['posx'], int)
                assert isinstance(self.target['posy'], int)
        self.player = player

    def verify_unit(self, units):
        '''check if id is correct and player owns unit'''
        assert self.id in units and units[self.id].player == self.player
        self.unit = units[self.id]

    def verify_target(self, units, map):
        '''make sure target is valid'''
        if isinstance(self.target, str):  # targeting a unit
            assert self.target in units and units[self.target].player != self.player
            target = units[self.target]
        elif isinstance(self.target, dict):  # targeting a tile (position)
            assert self.unit.mobile
            target = map.get_tile(self.target['posx'], self.target['posy'])
        assert map.player_has_vision(self.player, target)
        self.target = target

    def execute(self):
        if self.action is ActionType.target:
            self.unit.set_target(self.target)
        elif self.action is ActionType.clear_target:
            self.unit.clear_target()
        elif self.action is ActionType.stop:
            self.unit.stop()
        else:
            raise Exception('Uhm?')


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
        self.players = {0: self.player0, 1: self.player1}
        self.init_map()
        self.turn = 0
        self.spawn_interval = 10
        self._all_units = None

    @staticmethod
    def serialize(gamestate):
        return gzip.compress(pickle.dumps(gamestate), compresslevel=1)

    @staticmethod
    def deserialize(serialized):
        return pickle.loads(gzip.decompress(serialized))

    @property
    def all_units(self):
        '''resetted at the end of turn and regenerated at first access of every turn'''
        if self._all_units is None:
            self._all_units = self.map.get_all_units()
        return self._all_units

    @property
    def finished(self):
        p0, p1 = 0, 0  # unit counts
        for unit in self.all_units:
            if p0 and p1:
                return False
            if unit.player == self.player0:
                p0 += 1
            else:
                p1 += 1
        return True

    @property
    def winner(self):
        if not self.finished:
            return None
        if not self.all_units:
            return False
        return self.all_units[0].player

    def init_map(self):
        assert not hasattr(self, 'map') or self.map is None
        self.map = Map(p0=self.player0, p1=self.player1)

    def begin_turn(self):
        if self.turn % self.spawn_interval == 0:
            self._spawn_new_units()
        assert not self.finished, 'Game is finished'
        for unit in self.all_units:
            unit.action_points = 1

    def state_for_player(self, player):
        return dict(
            player_id=player.id, turn=self.turn,
            map=self.map.to_array(by_player=player),
        )

    def commands_from_player(self, player, commands):
        '''actions are limited to total unit count, extras will be trimmed
        from the beginning
        '''
        unit_lookup = {unit.id: unit for unit in self.all_units}
        actions = []
        errors = []  # TODO maybe feedback, maybe clear error definitions
        commands = commands[-1 * len(unit_lookup):]
        for command in commands:
            try:
                cmd = Command(player, command)
                cmd.verify_unit(unit_lookup)
                if cmd.action is ActionType.target:
                    cmd.verify_target(unit_lookup, self.map)
            except AssertionError:
                errors.append(command)
                continue
            cmd.execute()
            actions.append(command)
        return dict(actions=actions, errors=errors)

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
        for unit in self.all_units:
            if unit.target in dead_units:
                unit.clear_target()

    def evaluate_turn(self):
        '''execute planned actions for one turn'''
        for step in ('attack', 'move', 'chase', 'finish'):
            # NOTE: execution order by-tile, all actions need to be synced, otherwise can be unfair
            for unit in self.all_units:
                unit.end_of_turn(step)
        self._remove_dead_units()
        self._all_units = None
        self.turn += 1

    def ascii(self, pid=None):
        tmp_map = Map()
        if pid is not None:
            assert pid in (0, 1)
            player = self.player0 if pid == 0 else self.player1
            positions = self.map.vision_by_player(player)
        else:
            positions = None
        for y in range(self.map.size_y):
            for x in range(self.map.size_x):
                if not self.map.is_valid_position(x, y):
                    continue
                if positions is None or (x, y) in positions:
                    tmp_map.map[y][x] = self.map.get_tile(x, y)
                else:
                    tmp_map.map[y][x] = None

        return tmp_map.as_string()
