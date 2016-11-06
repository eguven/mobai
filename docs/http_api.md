# HTTP API

**Authentication is disabled** in early development, a user will be autocreated
if it doesn't already exist when someone queues with it.

### Queing for a game

**POST /api/queue**

Required JSON body fields: `username`, `bot`

    {"username": "<username>", "bot": "<bot>"}

### Getting state for game

**GET /api/games/\<gameid\>**

Required query arguments: `username`, `token`

### Posting commands for a game turn

**POST /api/games/\<gameid\>**

Required query arguments: `username`, `token`
Required fields: `commands`

    {"commands": [{...}]}

    # command structure is described in "Mobai JSON Data and Structure" document
