import tornado.ioloop
import tornado.web

from . import gamequeue
from . import handlers

routes = [
    (r'/api/queue', handlers.QueueHandler),
    (r'/api/games/([0-9a-f]*)', handlers.GameHandler),
]

if __name__ == '__main__':
    app = tornado.web.Application(routes)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().spawn_callback(gamequeue.MatchMaker().match_game)
    tornado.ioloop.IOLoop.current().start()
