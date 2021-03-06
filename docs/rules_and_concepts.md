# Mobai Rules and Concepts

### Building Type Units

Forts and Towers.

These units are immobile, have no path, and can not target ``GameTiles``. Also see
'AutoTargeting' section.

### Mobile Units

Soldiers.

### Unit Vision

Every unit has a `vision` property denoting how many tiles far it can see.

### Player Vision

Player vision is the collective vision of all player units. Anything outside player
vision is in Fog of War.

### Targeting

Player units can target enemy units if that enemy unit is within player vision. This means

1. the unit will attack its target if it can (further rules apply)
2. chase until 1 is true

If at any given turn the player loses vision of an enemy unit, _all player units
currently chasing that enemy unit will have their **target reset**_. They will however retain
their paths and continue along that route moving to the last known position of their targets.

#### Mobile vs Immobile Units

Mobile units can target game tiles which sets their path to that tile whereas
immobile units can only target units. Reached game tile targets are cleared automatically.

### Clear Target

Clearing target means resetting `attack when you can` (chase) order. Mobile units will
retain their paths and contiue moving.

### Stop

Reset the targets path. This also implies resetting a target due to targeting
mechanics ie. since units chase their targets, they would re-path.

For immobile units, this is identical to clearing a target.

### Attacking

Every unit has a `hit` property denoting how many tiles far it can attack. They also
have an `attack` property denoting the damage they will do to an enemy they attack.

### AutoTargeting

Building type units will auto-target an enemy unit they can hit, if they have no target
set and have action points available. This will happen after applying player actions and
before attack resolution. Building targets are cleared in chase resolution. See
Turn Resolution steps.

### Unit Death

At the end of each turn, any unit with health less or equal to zero will be removed
from the game map.

### Unit Generation

Every X (TBD) turns, Y (TBD) units will spawn into the game map at player Forts (might change).

### Game End

Player loses when it runs out of units.

### Turn Resolution

Every turn has the following steps

* Turn begin, resetting action points, spawning new units
* Players receive game state
* Players send actions
* Actions are verified, illegal actions are dropped
* Turn resolution
    * Attack resolution: Unit that can hit their targets will do so
    * Move resolution: Units that are mobile and have a path they can move to will do so
    * Chase resolution: Units that have their target still in vision will re-path to their target
* Dead units are removed from game map
* Units with dead targets have their targets reset
* Turn ends
