import logging
import random

import motor.motor_tornado

from tornado import gen
from tornado import ioloop

from .utils import create_token

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

mc = motor.motor_tornado.MotorClient(w=1)
gamequeue = mc.mobai.queue
games = mc.mobai.games


class MatchMaker(object):
    '''coroutine based mongodb backed matchmaker to be run within tornado'''
    @gen.coroutine
    def match_game(self):
        logger.info('Matchmaker starting')
        while True:
            wait = gen.sleep(5)
            starttime = ioloop.IOLoop.current().time()
            players = yield gamequeue.find().sort([('_id', 1)]).limit(10).to_list(length=10)
            while len(players) >= 2:
                random.shuffle(players)
                p0, p1, players = players[0], players[1], players[2:]
                p0['token'], p1['token'] = create_token(), create_token()
                queue_ids = [p0.pop('_id'), p1.pop('_id')]
                game = {'player0': p0, 'player1': p1, 'turn': 0, 'status': 'new'}
                yield games.insert_one(game)
                # TODO start game runner
                yield gamequeue.delete_many({'_id': {'$in': queue_ids}})
            endtime = ioloop.IOLoop.current().time()
            logger.debug('MatchMaker ran for %.3fms', 1000 * (endtime - starttime))
            yield wait


@gen.coroutine
def is_in_queue(user_oid, bot):
    found = yield gamequeue.find_one({'user': user_oid, 'bot': bot}, {'_id': 1})
    return bool(found)


@gen.coroutine
def add_to_queue(user_oid, bot):
    yield gamequeue.insert_one({'user': user_oid, 'bot': bot})


@gen.coroutine
def has_game_ready(user_oid, bot):
    game = yield games.find_one({'$or': [{'player0.user': user_oid, 'player0.bot': bot},
                                         {'player1.user': user_oid, 'player1.bot': bot}]})
    return game
