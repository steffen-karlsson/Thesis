# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import abstractmethod
from os import path

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, asynchronous, StaticFileHandler

from bdos.gateway import api, CLASS_ERROR
import bdos


def get_path():
    return path.dirname(path.abspath(bdos.__file__))


class ExpectedDatasetClassNotExists(Exception):
    pass


class RootHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self):
        self.set_status(200)
        self.render("%s/web/index.html" % get_path())


class DocumentationHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, *args):
        index = str(args[0]).strip()
        if not index:
            index = "index.html"

        self.set_status(200)
        self.render("%s/web/docs/_build/html/%s" % (get_path(), index))


TORNADO_SETTINGS = {
    r'static_path': r"%s/web/static" % get_path(),
    r'static_url_prefix': r'/static/',
}

TORNADO_ROUTES = [
    (r'/', RootHandler),
    (r"/docs/_static/(.*)", StaticFileHandler, {"path": "%s/web/docs/_build/html/_static" % get_path()}),
    (r'/docs/(.*)', DocumentationHandler),
]


class AbsPyAdminGateway(Application):
    # __metaclass__ = ABCMeta

    def __init__(self, gateway_uri):
        super(AbsPyAdminGateway, self).__init__()
        self.api = api(gateway_uri)

    def create_dataset(self, name, dataset_type_name):
        res = self.api.create(name, dataset_type_name)
        if res == CLASS_ERROR:
            raise ExpectedDatasetClassNotExists

    def append_to_dataset(self, name, url):
        self.api.append(name, url)

    @abstractmethod
    def get_available_datasets(self):
        pass

    def start_web(self, port, hostname='localhost'):
        Application.__init__(self, TORNADO_ROUTES, **TORNADO_SETTINGS)

        server = HTTPServer(self)
        server.listen(address=hostname, port=port)
        print "*** Running on localhost:%d" % port
        IOLoop.current().start()
