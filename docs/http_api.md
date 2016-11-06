# HTTP API

**Authentication is disabled** in early development, a user will be autocreated
if it doesn't already exist when someone queues with it.

### Queing for a game

**POST /api/queue**

Required fields are: `username`, `bot`

{"username": "<username>", "bot": "<bot>"}
