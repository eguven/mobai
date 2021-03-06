# MOBAI MongoDB Data Structures

### Games

    {
        '_id': ObjectId,
        'player0': {'user': ObjectId, 'bot': str, 'token': str},
        'player1': {'user': ObjectId, 'bot': str, 'token': str},
        'state': bytes,
        'turn': int,
        'status': str,
        'finish_reason': str,
    }

### Queue

    {
        '_id': ObjectId,
        'user': ObjectId,
        'bot': str,
    }

### Users

    {
        '_id': ObjectId,
        'username': str,
        'password': bytes,
    }

### Commands

Note: If filtering by game_player_id_turn becomes heavy, we move to concatenated _id

    {
        '_id': ObjectId,
        'game': ObjectId,
        'player_id': int,
        'turn': int,
        'commands': list,
    }

    # command structure identical to what is described in
    # "Mobai JSON Data and Structure" document
