import enum

from .base import Player
from .map import Map
from .tile import GameTile


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
        if isinstance(command.target, str):  # targeting a unit
            assert command.target in units and units[command.target].player != self.player:
            target = units[command.target]
        elif isinstance(command.target, dict):  # targeting a tile (position)
            assert self.unit.mobile
            target = map.get_tile(command.target['posx'], command.target['posy'])
        assert map.player_has_vision(target)
        self.target = target

    def execute(self):
        if self.action is ActionType.target:
            self.set_target(self.target)
        elif self.action is ActionType.clear_target:
            self.clear_target()
        elif self.action is ActionType.stop:
            self.stop()
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

    def commands_from_player(self, player, commands):
        '''actions are limited to total unit count, extras will be trimmed
        from the beginning
        '''
        unit_lookup = {unit.id: unit for unit in self.map.get_all_units()}
        actions = []
        errors = []  # TODO maybe feedback, maybe clear error definitions
        commands = commands[-1 * len(units):]
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
