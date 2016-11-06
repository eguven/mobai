import logging
import time

import click
from bson.objectid import ObjectId
from pymongo import MongoClient

from mobai.engine.game import GameState

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

mc = MongoClient(w=1)
games = mc.mobai.games
commands = mc.mobai.commands


class Runner(object):
    '''A game runner that retrieves player commands and progresses the game,
    mongodb backed
    '''
    @classmethod
    def start_game(cls, game_id):
        runner = cls(game_id)
        runner.run()

    def __init__(self, game_id):
        self.game_strid = game_id
        self.game_oid = ObjectId(self.game_strid)
        if not games.find_one(self.game_oid, {'_id': 1}):
            raise TypeError('Game "%s" doesn\'t exist' % self.game_strid)

    def get_gamestate(self):
        data = games.find_one({'_id': self.game_oid}, {'state': 1, '_id': 0})
        return GameState.deserialize(data['state'])

    def save_gamestate(self, gamestate):
        data = GameState.serialize(gamestate)
        games.update({'_id': self.game_oid}, {'$set': {'state': data}})

    def get_player_commands(self, player, turn):
        player_commands = commands.find_one({'game': self.game_oid, 'player_id': player.id, 'turn': turn},
                                            {'commands': 1, '_id': 0})
        return player_commands if player_commands is None else player_commands['commands']

    def run(self):
        # start game if necessary
        g_status = games.find_one({'_id': self.game_oid}, {'status': 1, '_id': 0})['status']
        if g_status == 'new':
            logger.info('Game "%s" is new, initializing', self.game_strid)
            gs = GameState()
            gs.begin_turn()
            games.update({'_id': self.game_oid},
                         {'$set': {'status': 'running', 'state': GameState.serialize(gs), 'turn': 0}})
            return self.run()
        elif g_status == 'finished':
            # TODO: merge commands into game
            logger.info('Game "%s" is finished, finalizing', self.game_strid)
            return

        while True:
            game = games.find_one(self.game_oid)
            gs = GameState.deserialize(game['state'])
            assert game['turn'] == gs.turn

            logger.info('Game "%s" loaded and running, waiting player commands', self.game_strid)
            p0commands, p1commands = None, None
            # now we wait for commands
            wait_start = time.time()
            while p0commands is None or p1commands is None:
                time.sleep(0.1)
                if p0commands is None:
                    p0commands = self.get_player_commands(gs.player0, gs.turn)
                if p1commands is None:
                    p1commands = self.get_player_commands(gs.player1, gs.turn)
                if p0commands or p1commands:
                    if time.time() - wait_start > 10:
                        # TODO: stop game
                        logger.info('Commands received\nP0commands: %s\nP1commands: %s\n',
                                    p0commands, p1commands)
                        pass
            p0_commands_result = gs.commands_from_player(gs.player0, p0commands)
            p1_commands_result = gs.commands_from_player(gs.player1, p1commands)
            # TODO persist errors (command results)
            logger.info('Commands applied\nP0: %s\nP1: %s', p0_commands_result, p1_commands_result)
            gs.evaluate_turn()
            assert gs.turn == game['turn'] + 1
            try:
                gs.begin_turn()
            except AssertionError:
                logger.info('Game "%s" has ended with winner %s', self.game_strid, gs.winner)
                state = GameState.serialize(gs)
                games.update({'_id': self.game_oid},
                             {'$set': {'state': state, 'turn': gs.turn, 'status': 'finished'}})
                return self.run()
            state = GameState.serialize(gs)
            games.update({'_id': self.game_oid},
                         {'$set': {'state': state, 'turn': gs.turn}})


@click.command()
@click.argument('game_id')
def run_game(game_id):
    Runner.start_game(game_id)

if __name__ == '__main__':
    run_game()
