class IDComparable(object):
    '''equality and uniqueness by id property'''
    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)


class Player(IDComparable):
    def __init__(self, id):
        self.id = id
        self._visible_tiles = []
        self._visible_positions = []

    def set_visible_tiles(self, tiles):
    	'''used to set player vision at the beginning of each turn'''
    	self._visible_tiles = tiles
    	self._visible_positions = [(tile.x, tile.y) for tile in tiles]

    def has_vision(self, target):
    	return (target.x, target.y) in self._visible_positions
