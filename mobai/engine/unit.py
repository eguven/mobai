import uuid

from .base import IDComparable


class UnitBase(IDComparable):
    '''Anything that sits on a GameTile is based on this, subclasses/mixins
    add further properties. `UUID4.hex` ids
    '''
    def __init__(self, player):
        self.id = str(uuid.uuid4())
        self.health = 0
        self.vision = 0
        self.hit = 0
        self.attack = 0
        self.target = None  # tile or unit
        self.action_points = 1

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

    @property
    def _map(self):
        return self._tile._map

    def to_dict(self, as_target=False):
        if as_target:
            return dict(
                id=self.id, posx=self.x, posy=self.y, type=self.__class__.__name__,
            )
        data = dict(
            id=self.id, posx=self.x, posy=self.y, type=self.__class__.__name__,
            target=self.target.to_dict(as_target=True) if self.target else None,
            health=self.health, vision=self.vision, hit=self.hit, attack=self.attack,
            action_points=self.action_points, player=self.player.id,
        )
        if hasattr(self, 'path'):
            data['path'] = [dict(posx=tile.x, posy=tile.y) for tile in self.path]
        return data

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

    def visible_units(self, non_player_only=False):
        units = []
        for tile in [self._tile._map.get_tile(*pos) for pos in self.visible_positions()]:
            if non_player_only:
                units.extend([unit for unit in tile.occupants if unit.player != self.player])
            else:
                units.extend(tile.occupants)
        return units

    def hittable_units(self):  # hittable? really?
        units = []
        for tile in [self._tile._map.get_tile(*pos) for pos in self.hit_positions()]:
            units.extend([unit for unit in tile.occupants if unit.player != self.player])
        return units

    def can_act(self):
        '''has action points'''
        assert 0 <= self.action_points
        return 0 < self.action_points

    def can_hit(self, target):
        assert isinstance(target, UnitBase)
        if self.player == target.player:
            return False
        pos = (target.x, target.y)
        return pos in self.hit_positions()

    def can_move_to(self, target):
        '''can the unit move to target (tuple/GameTile)'''
        # NOTE: needs change if we have units that can move >1 in a turn
        from .tile import GameTile
        assert isinstance(target, (tuple, GameTile))
        if not self.mobile:
            return False
        if isinstance(target, GameTile):
            return self._tile.is_neighbor(target)  # NOTE: would change for multi-action, maybe
        elif isinstance(target, tuple):
            return target in self._tile.neighbor_positions()

    def _set_attack_target(self, target):
        assert self._map.player_has_vision(self.player, target)
        assert self.player != target.player
        self.target = target

    def set_target(self, target):
        from .tile import GameTile
        if isinstance(target, GameTile):
            assert self.mobile
            self._set_move_target(target)
        else:
            self._set_attack_target(target)

    def clear_target(self):
        self.target = None

    def stop(self):
        '''stop whatever you're doing'''
        self.clear_target()

    def attack(self):
        '''attack current target, decrease action points and target health'''
        #  sanity checks with target
        assert self.target
        assert self.can_hit(self.target)
        assert 0 < self.action_points
        # actually attack
        self.target.health -= self.attack
        self.action_points -= 1

    def _turn_attack_step(self):
        '''units attack step in turn'''
        # if I'm a building with no target and available action points
        if isinstance(self, Building) and not self.target and self.can_act():
            self.try_autotarget()
        if isinstance(self.target, UnitBase) and self.can_hit(self.target) and self.can_act():
            self.attack()

    def _turn_move_step(self):
        '''units move step in turn'''
        if not self.mobile:
            assert not hasattr(self, 'path')
            return
        # mobile, have path, can move, have action points
        elif self.path and self.can_move_to(self.path[0]) and self.can_act():
            self.move(self.path[0])
            return
        # sanity-check
        elif self.path and not self.can_move_to(self.path[0]):
            # this should't really happen right? like, did I teleport?
            print('WTF: next tile in path unreachable', self, type(self), self.id)  # TODO: logging
            self.path = []
            return

    def _turn_chase_step(self):
        '''chase as in re-path to target, does not move, does not require action points'''
        if not isinstance(self.target, UnitBase):
            return
        elif self._map.player_has_vision(self.player, self.target) and self.mobile:
            self.set_target(self.target)  # re-path
        else:
            # either I'mma building, or I lost the guy #foreveralone
            self.clear_target()

    def end_of_turn(self, step):
        if step == 'attack':
            self._turn_attack_step()
        elif step == 'move':
            self._turn_move_step()
        elif step == 'chase':
            self._turn_chase_step()
        else:
            raise AssertionError('Uhm?')


class Building(object):
    def move(self, *args):
        raise TypeError

    def try_autotarget(self):
        '''try to set a target I can hit'''
        assert not self.target
        can_attack = self.hittable_units()
        if can_attack:
            self.set_target(can_attack[0])


class Tower(Building, UnitBase):
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

    def spawn_soldiers(self, count=0):
        for _ in range(count):
            self._tile.add_unit(Soldier(self.player))


class Soldier(UnitBase):
    def __init__(self, *args):
        super(Soldier, self).__init__(*args)
        self.health = 3
        self.vision = 2
        self.hit = 1
        self.attack = 1
        self.path = []

    def move(self, next_tile):
        '''move unit between tiles'''
        assert self.mobile
        assert self.path and self.path[0] == next_tile
        assert self._tile.is_neighbor(next_tile)
        assert 0 < self.action_points
        self._tile.remove_unit(self)
        next_tile.add_unit(self)
        self.path = self.path[1:]
        self.action_points -= 1

    def _set_move_target(self, target):
        if self._tile == target:
            assert not self.path  # sanity
            return  # TODO: might use for feedback
        self.path = self._tile.path_to(target)
        self.target = target

    def _set_attack_target(self, target):
        super(Soldier, self)._set_attack_target(target)  # would raise if not if vision
        self._set_move_target(target._tile)

    def stop(self):
        super(Soldier, self).stop()
        self.path = []
