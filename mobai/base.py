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
