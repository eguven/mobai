from .unit import Building


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
