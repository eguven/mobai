import uuid

import numpy

from util import a_star_search


class IDComparable(object):
    '''equality and uniqueness by id property'''
    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)


class UnitBase(IDComparable):
    '''Anything that sits on a GameTile is based on this, subclasses/mixins
    add further properties. `UUID4.hex` ids
    '''
    def __init__(self, player):
        self.id = uuid.uuid4().hex
        self.health = 0
        self.vision = 0
        self.hit = 0
        self.attack = 0
        self.player = player
        self._tile = None

    @property
    def x(self):
        return self._tile.x

    @property
    def y(self):
        return self._tile.y

    @property
    def mobile(self):
        return not isinstance(self, Building)

    def positions_within_range(self, reach):
        positions = set()
        x, y = self.x, self.y
        positions.add((x, y))
        for delta in range(1, reach + 1):
            for p in [(x + delta, y), (x, y + delta), (x - delta, y), (x, y - delta)]:
                if self._tile._map.is_valid_position(*p):
                    positions.add(p)
        return positions

    def visible_positions(self):
        '''can see/within vision value'''
        return self.positions_within_range(self.vision)

    def hit_positions(self):
        '''within hit value'''
        return self.positions_within_range(self.hit)

    def visible_units(self):
        units = []
        for tile in [self._tile._map.get_tile(*pos) for pos in self.visible_positions()]:
            units.extend(tile.occupants)
        return units

    def is_in_vision(self, target):
        '''is the target (UnitBase/GameTile) visible'''
        assert isinstance(target, (UnitBase, GameTile))
        pos = (target.x, target.y)
        return pos in self.visible_positions()

    def can_hit(self, target):
        assert isinstance(target, UnitBase)
        pos = (target.x, target.y)
        return pos in self.hit_positions()

    def can_move_to(self, target):
        '''can the unit move to target (tuple/GameTile)'''
        # NOTE: needs change if we have units that can move >1 in a turn
        assert isinstance(target, (tuple, GameTile))
        if not self.mobile:
            return False
        if isinstance(target, GameTile):
            return self.is_neighbor(target)
        elif isinstance(target, tuple):
            return target in self.neighbor_positions()

    def attack(target=None):
        # if no target, prio building > superunit > unit
        pass


class Building(object):
    def move(self, *args):
        raise NotImplementedError


class Tower(UnitBase, Building):
    def __init__(self, *args):
        super(Tower, self).__init__(*args)
        self.health = 100
        self.vision = 2
        self.hit = 1
        self.attack = 5


class Fort(Tower):
    def __init__(self, *args):
        super(Fort, self).__init__(*args)
        self.health = 150
        self.vision = 3
        self.attack = 5


class Unit(UnitBase):
    def __init__(self, *args):
        super(Unit, self).__init__(*args)
        self.health = 3
        self.vision = 2
        self.hit = 1
        self.attack = 1
        self.target = None  # tile or unit
        self.path = []

    def move(self, next_tile):
        '''move unit between tiles'''
        assert self.path and self.path[0] == next_tile
        assert self._tile.is_neighbor(next_tile)
        self._tile.remove_unit(self)
        next_tile.add_unit(self)
        self.path = self.path[1:]

    def _set_move_target(self, target):
        if self._tile == target:
            return  # TODO: might use for feedback
        self.path = self._tile.path_to(target)
        self.target = target

    def _set_attack_target(self, target):
        raise NotImplementedError

    def set_target(self, target):
        if isinstance(target, GameTile):
            self._set_move_target(target)
        else:
            # Check if in vision to set
            # + chasing considerations, vision during chase, as well as action/move/unit evaluation order
            # maybe set_target for tile and re-evaluate path every turn
            raise NotImplementedError

    def end_of_turn(self):
        raise NotImplementedError


class Player(IDComparable):
    def __init__(self, id):
        self.id = id


class GameTile(object):
    '''A tile in map. Has position (reverse of array indices) and occupants'''
    def __init__(self, x=None, y=None, occupants=None, _map=None):
        assert x is not None and y is not None
        self.x = x
        self.y = y
        self.occupants = occupants if occupants is not None else []
        self._map = _map

    # reasonable but will not until a concrete use-case arises
    # def __hash__(self):
    #     return hash((self.x, self.y))

    def __str__(self):
        return 'GameTile(%dx%d)' % (self.x, self.y)

    def add_unit(self, unit):
        assert unit not in self.occupants
        if isinstance(unit, Building):
            tile_buildings = [tile_unit for tile_unit in self.occupants if isinstance(tile_unit, Building)]
            assert not tile_buildings
        unit._tile = self
        self.occupants.append(unit)

    def remove_unit(self, unit):
        assert unit in self.occupants
        assert not isinstance(unit, Building)
        self.occupants.remove(unit)
        unit._tile = None

    def grid_index(self):
        '''in 2d array, x is the second index (column) and y is the first (row)'''
        return (self.y, self.x)

    def neighbor_positions(self):
        # TODO: maybe right side tiles start neighbor list at 9-oclock (-1, 0)
        # while left side tiles start at 3 oclock (+1, 0) for symmetry
        x, y = self.x, self.y
        positions = [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]
        return [pos for pos in positions if self._map.is_valid_position(*pos)]

    def is_neighbor(self, tile):
        tile_pos = (tile.x, tile.y)
        return tile_pos in self.neighbor_positions()

    def path_to(self, tile):
        return self._map.shortest_path(self, tile)

    def units_by_player(self, player, filters=None, sort_key=None):
        '''return an iterable of units of the tile for player, optional filter:
        `if unit.__class___ in filters`
        '''
        player_units = [unit for unit in self.occupants if unit.player == player]
        if filters is not None and filters:
            player_units = [unit for unit in player_units if unit.__class__ in filters]
        if sort_key is not None and callable(sort_key):
            player_units = sorted(player_units, key=sort_key)
        return player_units


class Map(object):
    '''The Game map. 36x21 (default), 7:4 ratio with building placements as follows:
    X: 0, 2, 5, 7
    Y: 0, 2, 4
    Buildings on either side are Forts
    '''
    x_y_ratio = (7, 4)

    def __init__(self, x=36, y=21, p0=None, p1=None):
        assert (x - 1) % self.x_y_ratio[0] == 0
        assert (y - 1) % self.x_y_ratio[1] == 0
        self.size_x, self.size_y = x, y

        # depends on ratio ([0, 10, 25, 35], [0, 10 , 20])
        # self.building_x_markers = ((self.size_x - 1) / self.x_y_ratio[0]) * [0, 2, 5, 7]
        # self.building_y_markers = ((self.size_y - 1) / self.x_y_ratio[1]) * [0, 2, 4]
        x_step = int((self.size_x - 1) / self.x_y_ratio[0])
        y_step = int((self.size_y - 1) / self.x_y_ratio[1])
        self.building_x_markers = numpy.multiply(x_step, [0, 2, 5, 7])
        self.building_y_markers = numpy.multiply(y_step, [0, 2, 4])

        self.map = numpy.ndarray((self.size_y, self.size_x), dtype=GameTile)
        for y in range(self.size_y):
            for x in range(self.size_x):
                if self.is_valid_position(x, y):
                    self.map[y][x] = GameTile(x=x, y=y, _map=self)

        if p0 is not None and p1 is not None:
            self.init_buildings(p0, p1)

    def init_buildings(self, p0, p1):
        assert isinstance(p0, Player)
        assert isinstance(p1, Player)
        positions = []
        for x in self.building_x_markers:
            for y in self.building_y_markers:
                positions.append((x, y))
        for x, y in positions:
            # min/max x has Forts, others are Towers
            player = p0 if self.is_position_player_side(x, y, p0) else p1
            if x == 0 or x == self.size_x - 1:
                self.map[y][x].add_unit(Fort(player))
            else:
                self.map[y][x].add_unit(Tower(player))

    def vision_by_player(self, player):
        in_vision_positions = set()
        # iterate over map
        for y in range(self.size_y):
            for x in range(self.size_x):
                # make sure it's a valid tile
                if self.map[y][x] is None:
                    continue
                # get players units
                units = self.map[y][x].units_by_player(player, sort_key=lambda u: u.vision)
                if not units:
                    continue
                # use the unit with max vision to calculate
                max_vision_unit = units[-1]
                in_vision_positions.update(max_vision_unit.visible_positions())
        return in_vision_positions

    def tiles_visible_by_player(self, player):
        # sorted in direction right > bottom
        tiles = []
        positions = sorted(
            sorted(self.vision_by_player(player), key=lambda p: p[1]),
            key=lambda p: p[0])
        for x, y in positions:
            tiles.append(self.map[y][x])
        return tiles

    def is_valid_position(self, x, y):
        '''is position within boundaries and does it share an X or Y with any
        building, which suggests a lane
        '''
        if x < 0 or y < 0:
            return False
        max_y, max_x = self.map.shape
        if x >= max_x or y >= max_y:
            return False
        if x in self.building_x_markers or y in self.building_y_markers:
            return True
        return False

    def is_position_player_side(self, x, y, player):
        '''left half is player0, right half is player1'''
        if self.size_x % 2 == 1:
            raise NotImplementedError
        return (player.id == 0 and x < self.size_x / 2) or (player.id == 1 and x >= self.size_x / 2)

    def get_tile(self, x, y):
        assert self.is_valid_position(x, y), 'x=%s y=%s is not a valid position' % (x, y)
        return self.map[y][x]

    def get_neighbors_of_tile(self, tile):
        return [self.get_tile(x, y) for x, y in tile.neighbor_positions()]

    def shortest_path(self, start, end):
        '''Returns the list of steps on the shortest path between start and end.
        Works with GameTile or tuples, return type will match be the input type
        '''
        assert type(start) == type(end)
        assert isinstance(start, (tuple, GameTile))
        if isinstance(start, GameTile):
            path = a_star_search(self, (start.x, start.y), (end.x, end.y))
            return [self.get_tile(*pos) for pos in path]
        return a_star_search(self, start, end)

    def as_string(self):
        '''ascii is not dead'''
        chars = []
        for y in range(self.size_y):
            for x in range(self.size_x):
                if self.map[y][x] is None:
                    chars.append(' ')
                    continue

                occupants = self.map[y][x].occupants
                # this would be incorrect if a new type were added in between Fort and Tower
                if [u for u in occupants if isinstance(u, Fort)]:
                    chars.append('F')
                elif [u for u in occupants if isinstance(u, Tower)]:
                    chars.append('T')
                else:
                    chars.append('·')
            chars.append('\n')
        return ' ' + ' '.join(chars)


class GameState(object):
    def __init__(self):
        self.player0, self.player1 = Player(0), Player(1)
        self.map = self.init_map()

    def init_map(self):
        assert not hasattr(self, 'map') or self.map is None
        self.map = Map(p0=self.player0, p1=self.player1)

    def state_for_player(self, player):
        pass
