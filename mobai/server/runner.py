import logging
import time

import click
from bson.objectid import ObjectId
from pymongo import MongoClient

from mobai.engine.game import GameState

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

TURN_TIMEOUT_SECONDS = 10

mc = MongoClient(w=1)
games = mc.mobai.games
commands = mc.mobai.commands


class Runner:
    """A game runner that retrieves player commands and progresses the game, mongodb backed"""

    @classmethod
    def start_game(cls, game_id):
        runner = cls(game_id)
        runner.run()

    def __init__(self, game_id):
        self.game_strid = game_id
        self.game_oid = ObjectId(self.game_strid)
        self.finish_reason = None
        if not games.find_one(self.game_oid, {"_id": 1}):
            raise TypeError(f'Game "{self.game_strid}" doesn\'t exist')

    def get_gamestate(self):
        data = games.find_one({"_id": self.game_oid}, {"state": 1, "_id": 0})
        return GameState.deserialize(data["state"])

    def save_gamestate(self, gamestate):
        data = GameState.serialize(gamestate)
        games.update({"_id": self.game_oid}, {"$set": {"state": data}})

    def get_player_commands(self, player, turn):
        player_commands = commands.find_one(
            {"game": self.game_oid, "player_id": player.id, "turn": turn}, {"commands": 1, "_id": 0}
        )
        return player_commands if player_commands is None else player_commands["commands"]

    def run(self):
        # start game if necessary
        g_status = games.find_one({"_id": self.game_oid}, {"status": 1, "_id": 0})["status"]
        if g_status == "new":
            logger.info('Game "%s" is new, initializing', self.game_strid)
            gs = GameState()
            gs.begin_turn()
            games.update(
                {"_id": self.game_oid}, {"$set": {"status": "running", "state": GameState.serialize(gs), "turn": 0}}
            )
            return self.run()
        elif g_status == "finished":
            # TODO: merge commands into game
            logger.info('Game "%s" is finished, finalizing', self.game_strid)
            return

        while True:
            game = games.find_one(self.game_oid)
            gs = GameState.deserialize(game["state"])
            assert game["turn"] == gs.turn

            logger.info('Game "%s" turn "%d" loaded and running, waiting commands', self.game_strid, game["turn"])
            p0commands, p1commands = None, None
            # now we wait for commands
            wait_start = time.time()
            while p0commands is None or p1commands is None:
                time.sleep(0.1)
                if p0commands is None:
                    p0commands = self.get_player_commands(gs.player0, gs.turn)
                if p1commands is None:
                    p1commands = self.get_player_commands(gs.player1, gs.turn)
                # once at least one player has submitted, start the timeout clock
                # NOTE: this None vs [] setup is brittle, properly implement later
                if (
                    p0commands is not None or p1commands is not None
                ) and time.time() - wait_start > TURN_TIMEOUT_SECONDS:
                    timed_out = [p for p, cmds in [(0, p0commands), (1, p1commands)] if cmds is None]
                    logger.info(
                        'Game "%s" turn "%d" timed out, missing commands from player(s): %s',
                        self.game_strid,
                        game["turn"],
                        timed_out,
                    )
                    self.finish_reason = "timeout"
                    if p0commands is None:
                        p0commands = []
                    if p1commands is None:
                        p1commands = []
            logger.info('Game "%s" turn "%d" applying commands', self.game_strid, game["turn"])
            _p0_commands_result = gs.commands_from_player(gs.player0, p0commands)
            _p1_commands_result = gs.commands_from_player(gs.player1, p1commands)
            # TODO persist errors (command results)
            logger.info('Game "%s" turn "%d" advancing turn', self.game_strid, game["turn"])
            gs.evaluate_turn()
            assert gs.turn == game["turn"] + 1
            try:
                gs.begin_turn()
            except AssertionError:
                finish_reason = self.finish_reason or "victory"
                logger.info('Game "%s" has ended, reason: %s, winner: %s', self.game_strid, finish_reason, gs.winner)
                state = GameState.serialize(gs)
                games.update(
                    {"_id": self.game_oid},
                    {"$set": {"state": state, "turn": gs.turn, "status": "finished", "finish_reason": finish_reason}},
                )
                return self.run()
            state = GameState.serialize(gs)
            games.update({"_id": self.game_oid}, {"$set": {"state": state, "turn": gs.turn}})


@click.command()
@click.argument("game_id")
def run_game(game_id):
    Runner.start_game(game_id)


if __name__ == "__main__":
    run_game()
