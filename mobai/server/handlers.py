import json
import logging

import tornado.web
from tornado import gen

from bson.objectid import ObjectId, InvalidId
import motor.motor_tornado

from mobai.server.gamequeue import is_in_queue, add_to_queue, has_game_ready
from mobai.engine.game import GameState

mc = motor.motor_tornado.MotorClient(w=1)
users = mc.mobai.users
games = mc.mobai.games
commands = mc.mobai.commands


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
            self.set_status_and_write(400, {'error': 'bad request body'})
            raise

    def set_status_and_write(self, status, to_write):
        self.set_status(status)
        self.write(to_write)


class QueueHandler(BaseHandler):
    @gen.coroutine
    def authenticate_user(self):
        # skip auth for now, just require username and bot
        # early dev: insert user automatically
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
            self.set_status_and_write(400, {'error': 'username or bot fields not provided'})
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


class GameHandler(BaseHandler):

    @gen.coroutine
    def _set_game_and_player_designation(self, game_id, username, token):
        '''Make sure game exists and the provided username-token combination
        has rights to it. Set game and player_id and return True if yes, return
        None otherwise.
        '''
        try:  # correct game id and game existence
            game = yield games.find_one({'_id': ObjectId(game_id)})
        except InvalidId:
            game = None
        if game is None:
            self.set_status_and_write(404, {'error': 'game not found'})
            return

        # authorization to get game & player designation
        user = yield users.find_one({'username': username})
        if user and user['_id'] == game['player0']['user'] and token == game['player0']['token']:
            player_id = 0
        elif user and user['_id'] == game['player1']['user'] and token == game['player1']['token']:
            player_id = 1
        else:
            self.set_status_and_write(401, {'error': 'unauthorized (username or token mismatch)'})
            return

        self.game, self.player_id = game, player_id
        return True

    @gen.coroutine
    def get(self, game_id):
        try:  # required query parameters
            username = self.get_query_argument('username')
            token = self.get_query_argument('token')
        except tornado.web.MissingArgumentError as e:
            self.set_status_and_write(400, {'error': 'missing argument \'%s\'' % e.arg_name})
            return

        if not (yield self._set_game_and_player_designation(game_id, username, token)):
            return

        gs = GameState.deserialize(self.game['state'])
        # temp
        gs.players = {0: gs.player0, 1: gs.player1}
        map_for_player = gs.map.to_array(by_player=gs.players[self.player_id])
        data = dict(
            player_id=self.player_id,
            game_status=self.game['status'],
            turn=self.game['turn'],
            map=map_for_player,
        )
        self.write(data)

    @gen.coroutine
    def post(self, game_id):
        try:  # required query parameters
            username = self.get_query_argument('username')
            token = self.get_query_argument('token')
        except tornado.web.MissingArgumentError as e:
            self.set_status_and_write(400, {'error': 'missing argument \'%s\'' % e.arg_name})
            return

        try:
            self._decode_json_body()
        except json.decoder.JSONDecodeError:
            return

        if 'commands' not in self._data or not isinstance(self._data['commands'], list):
            print(self._data['commands'])
            self.set_status_and_write(400, {'error': 'commands property doesn\'t exist or is not a list'})
            return

        if not (yield self._set_game_and_player_designation(game_id, username, token)):
            return

        # check if there are already commands (runner waiting on other player)
        query = {'game': self.game['_id'], 'player_id': self.player_id, 'turn': self.game['turn']}
        turn_commands = yield commands.find_one(query, {'_id': 1})
        if turn_commands:
            errmsg = 'Enhance your calm, you\'ve already sent commands for this turn (%s)' % self.game['turn']
            self.set_status_and_write(400, {'error': errmsg})
            return

        doc = dict(
            game=self.game['_id'],
            turn=self.game['turn'],
            player_id=self.player_id,
            commands=self._data['commands'],
        )

        yield commands.insert_one(doc)
        self.write({'status': 'commands saved'})
