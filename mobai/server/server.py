import tornado.ioloop
import tornado.web

from . import gamequeue
from . import handlers

routes = [
    (r'/api/queue', handlers.QueueHandler)
]

if __name__ == '__main__':
    app = tornado.web.Application(routes)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().spawn_callback(gamequeue.MatchMaker().match_game)
    tornado.ioloop.IOLoop.current().start()
