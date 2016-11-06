import json
import logging

import tornado.web
from tornado import gen

import motor.motor_tornado

from mobai.server.gamequeue import is_in_queue, add_to_queue, has_game_ready

mc = motor.motor_tornado.MotorClient(w=1)
users = mc.mobai.users
games = mc.mobai.games


class WTFException(Exception):
    '''you know... for those extra special moments'''
    pass


class BaseHandler(tornado.web.RequestHandler):
    def _decode_json_body(self):
        '''Try to decode json body and set attribute. Write error if cannot'''
        try:
            self._data = tornado.escape.json_decode(self.request.body)
        except json.decoder.JSONDecodeError as e:
            logging.info('%s from decoding body "%s"', repr(e), self.request.body)
            self.set_status(400)
            self.write({'error': 'bad request body'})
            raise


class QueueHandler(BaseHandler):
    @gen.coroutine
    def authenticate_user(self):
        # skip auth for now, just require username and bot
        data = self._data
        if 'username' in data and data['username'] and 'bot' in data and data['bot']:
            username = data['username']
            user = yield users.find_one({'username': username})
            if not user:
                yield users.insert_one({'username': username})
                logging.info('Username "%s" autoinserted', username)
                user = yield users.find_one({'username': username})
            return user
        return False

    @gen.coroutine
    def post(self):
        try:
            self._decode_json_body()
        except json.decoder.JSONDecodeError:
            return
        user = yield self.authenticate_user()
        if not user:
            self.set_status(400)
            self.write({'error': 'username or bot fields not provided'})
            return

        game = yield has_game_ready(user['_id'], self._data['bot'])
        if game:
            # there is a game started by MatchMaker
            if user['_id'] == game['player0']['user'] and self._data['bot'] == game['player0']['bot']:
                player_id = 0
                token = game['player0']['token']
            elif user['_id'] == game['player1']['user'] and self._data['bot'] == game['player1']['bot']:
                player_id = 1
                token = game['player1']['token']
            else:
                emsg = 'user "%s" did not match any players in game "%s"'
                logging.error(emsg, user, game)
                raise WTFException(emsg, user['_id'], game['_id'])
            resp = {'player_id': player_id, 'token': token, 'game_id': str(game['_id'])}
            self.write(resp)
            return
        elif not (yield is_in_queue(user['_id'], self._data['bot'])):
            # add to queue
            yield add_to_queue(user['_id'], self._data['bot'])
            logging.info('Username-bot "%s-%s" added to queue', user['username'], self._data['bot'])
        else:
            logging.info('Username-bot "%s-%s" already in queue', user['username'], self._data['bot'])
        yield gen.sleep(10)
        self.write({'status': 'waiting in queue'})
