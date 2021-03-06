from .base import Player
from .tile import GameTile
from .unit import Fort, Tower, Soldier
from .util import a_star_search


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

        # self.building_x_markers = numpy.multiply(x_step, [0, 2, 5, 7])
        self.building_x_markers = [x_step * i for i in [0, 2, 5, 7]]
        # self.building_y_markers = numpy.multiply(y_step, [0, 2, 4])
        self.building_y_markers = [y_step * i for i in [0, 2, 4]]
        # self.map = numpy.ndarray((self.size_y, self.size_x), dtype=GameTile)
        self.map = [[None for x in range(self.size_x)] for y in range(self.size_y)]

        for y in range(self.size_y):
            for x in range(self.size_x):
                if self.is_valid_position(x, y):
                    self.map[y][x] = GameTile(x=x, y=y, _map=self)

        if p0 is not None and p1 is not None:
            self.init_buildings(p0, p1)

    def init_buildings(self, p0, p1):
        assert isinstance(p0, Player)
        assert isinstance(p1, Player)
        self.fort_positions, self.tower_positions = [], []
        positions = []
        for x in self.building_x_markers:
            for y in self.building_y_markers:
                positions.append((x, y))
        for x, y in positions:
            # min/max x has Forts, others are Towers
            player = p0 if self.is_position_player_side(x, y, p0) else p1
            if x == 0 or x == self.size_x - 1:
                self.map[y][x].add_unit(Fort(player))
                self.fort_positions.append((x, y))
            else:
                self.map[y][x].add_unit(Tower(player))
                self.tower_positions.append((x, y))

    def tiles(self):
        for y in range(self.size_y):
            for x in range(self.size_x):
                # make sure it's a valid tile
                if self.map[y][x] is None:
                    continue
                yield self.map[y][x]

    def vision_by_player(self, player):
        in_vision_positions = set()
        for tile in self.tiles():
            units = tile.units_by_player(player, sort_key=lambda u: u.vision)
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

    def player_has_vision(self, player, target):
        pos = target if isinstance(target, tuple) else (target.x, target.y)
        return pos in self.vision_by_player(player)

    def is_valid_position(self, x, y):
        '''is position within boundaries and does it share an X or Y with any
        building, which suggests a lane
        '''
        if x < 0 or y < 0:
            return False
        if x >= self.size_x or y >= self.size_y:
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

    def get_all_units(self, by_player=None):
        units = []
        for tile in self.tiles():
            if by_player is not None:
                units.extend([unit for unit in tile.occupants if unit.player == by_player])
            else:
                units.extend(tile.occupants)
        return units

    def get_forts(self, by_player=None):
        all_forts = []
        for x, y in self.fort_positions:
            all_forts.extend([unit for unit in self.map[y][x].occupants if isinstance(unit, Fort)])
        assert len(all_forts) <= 6  # sanity-check
        if by_player is not None:
            return [fort for fort in all_forts if fort.player == by_player]
        return all_forts

    def to_array(self, by_player=None):
        data = [[None for x in range(self.size_x)] for y in range(self.size_y)]
        if by_player is not None:
            player_vision = self.vision_by_player(by_player)
        for y in range(self.size_y):
            for x in range(self.size_x):
                if self.map[y][x] is None or (by_player is not None and (x, y) not in player_vision):
                    data[y][x] = None
                else:
                    data[y][x] = self.map[y][x].to_dict()
        return data

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
                elif [u for u in occupants if isinstance(u, Soldier)]:
                    chars.append('S')
                else:
                    chars.append('·')
            chars.append('\n')
        return ' ' + ' '.join(chars)
