# Mobai JSON Data and Structure

The values here are example data types, not necessarily accurate unit stats.

## Unit

Unit is an umbrella term covering any entity on the game map that can
take actions. All units have a unique ID, position, player and stats.

    # type: 'Soldier' | 'Tower' | 'Fort'

## Soldier

A mobile, soldier type unit.

    {
        'id': '4edb526b-42b5-4224-ab92-204b39379276',
        'posx': 0,
        'posy': 0,
        'type': 'Soldier',
        'target': {'id': '4ffbd1e8-19e5-45c3-abf7-9330877df3ee', 'type': 'Fort', 'posx': 35, 'posy': 20},
        'path': [{'posx': 0, 'posy': 1}, {'posx': 0, 'posy': 2}, ...],
        'health': 10,
        'vision': 2,
        'hit': 1,
        'attack': 3,
        'action_points': 1,
        'player': 0,
    }
    
    # target.type: 'Soldier' | 'Tower' | 'Fort' | 'GameTile'

Targets of type ``GameTile`` have no ID.

## Tower / Fort

An immobile, building type unit.

Building type units **will not have a path and can not target ``GameTiles``
(eg. position)**. Such action requests will result in no action taken for the respective
turn. See Rules and Concepts document for further information.

Apart from this exception, their data is identical to that of a ``Soldier``, and ``Forts``
are simply stronger towers.

## GameTile

A tile in the game map that has a position and a list of occupants. A tile can be
moved to.

    {
        'posx': 0,
        'posy': 0,
        'occupants': [
            {
                'id': '4edb526b-42b5-4224-ab92-204b39379276',
                'posx': 0,
                'posy': 0,
                'type': 'Soldier',
                ...
            },
            {
                'id': '9a62ecee-cc85-4579-8097-82d0b087bd7e',
                'posx': 0,
                'posy': 0,
                'type': 'Fort',
                ...
            },
            ...
        ]
    }

A player will only see occupants **if the ``GameTile`` is within vision**. See
Rules and Concepts document for further information.

## Map

    A Simple representation, 36x21
    
     F--10--T--15--T--10--F
     |      |      |      |
    10     10     10     10
     |      |      |      |
     F--10--T--15--T--10--F
     |      |      |      |
    10     10     10     10
     |      |      |      |
     F--10--T--15--T--10--F
    
     F: Fort
     T: Tower
     Paths are horizontal and vertical, empty space (most of the map) is null tiles.


A 2D array representing game tiles.

* A null object in the map represents the lack of tile eg. no path.
* Position ``{'posx': 0, 'posy': 0}`` represents to **top-left** corner of the map.
* The dimensions of the map currently is ``(36, 21)``.

Note that map indices are reversed, eg. a ``GameTile`` with position ``(x, y)`` is ``map[y][x]``.

    [
        ## x = 0-35, y = 0
        [
            {'posx': 0, 'posy': 0, 'occupants': [...]},
            {'posx': 1, 'posy': 0, 'occupants': [...]},
            ...,
            {'posx': 34, 'posy': 0, 'occupants': [...]},
            {'posx': 35, 'posy': 0, 'occupants': [...]},
        ],
        ## x = [0, 10, 25, 35], y = 1
        [
            {'posx': 0, 'posy': 1, 'occupants': [...]},
            null, null, null, null, null, null, null, null, null,
            {'posx': 10, 'posy': 1, 'occupants': [...]},
            null, null, null, null, null, null, null, null, null, null, null, null, null, null,
            {'posx': 25, 'posy': 1, 'occupants': [...]},
            null, null, null, null, null, null, null, null, null,
            {'posx': 35, 'posy': 1, 'occupants': [...]},
        ],
    
        ...,
    
        ## x = [0, 10, 25, 35], y = 19
        [
            {'posx': 0, 'posy': 19, 'occupants': [...]},
            null, null, null, null, null, null, null, null, null,
            {'posx': 10, 'posy': 19, 'occupants': [...]},
            null, null, null, null, null, null, null, null, null, null, null, null, null, null,
            {'posx': 25, 'posy': 19, 'occupants': [...]},
            null, null, null, null, null, null, null, null, null,
            {'posx': 35, 'posy': 19, 'occupants': [...]},
        ],
        ## x = 0-35, y = 20
        [
            {'posx': 0, 'posy': 20, 'occupants': [...]},
            {'posx': 1, 'posy': 20, 'occupants': [...]},
            ...,
            {'posx': 34, 'posy': 20, 'occupants': [...]},
            {'posx': 35, 'posy': 20, 'occupants': [...]},
        ]
    ]

## GameState

This is the object each player receives at the beginning of the turn.

    {
        'player_id': 0,                    # id of current player, 0-1
        'turn': 1,                         # current turn 0-
        'map': Map[21][36],                # game map as defined above
    }
