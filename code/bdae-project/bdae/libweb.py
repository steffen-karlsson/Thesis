# Created by Steffen Karlsson on 03-28-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libs
"""

from ujson import dumps, loads
from os import path
from base64 import b64encode

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, asynchronous, StaticFileHandler

from sofa.error import DatasetAlreadyExistsException
from bdae.libpy.libbdaeadmin import PyBDAEAdmin
from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist

GW = None


def get_static_path():
    return path.dirname(path.abspath(__file__))


class _RootHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self):
        self.set_status(200)
        self.render("%s/web/index.html" % get_static_path())


class _RegisteredDatasetHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    def compute_etag(self):
        return None

    @asynchronous
    def get(self):
        datasets = GW.get_datasets()

        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(dumps(list() if datasets is None else datasets))


class _OperationsHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, dataset_name):
        operations = GW.get_operations(dataset_name)

        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(dumps(list() if operations is None else operations))


class _CreateDatasetHandler(RequestHandler):
    @asynchronous
    def post(self, *args, **kwargs):
        body = dict(loads(self.request.body))

        message = ""
        try:
            res = GW.create_dataset(body['dataset-name'], body['dataset-type'])
        except DatasetAlreadyExistsException as e:
            res = 409
            message = e.message
        except NotImplementedError as e:
            res = 405
            message = e.message

        self.set_status(res)
        self.finish(message)


class _DeleteDatasetHandler(RequestHandler):
    @asynchronous
    def delete(self, *args, **kwargs):
        pass


class _UpdateDatasetHandler(RequestHandler):
    @asynchronous
    def post(self, *args, **kwargs):
        pass


class _JobHandler(RequestHandler):
    @asynchronous
    def post(self, *args, **kwargs):
        body = dict(loads(self.request.body))

        if body['is-polling']:
            status, res = GW.poll_for_result(body['dataset-name'], body['function-name'], body['query'])
            self.set_status(status)
            if res[1]:
                with open(res[0], "rb") as f:
                    self.finish(dumps({'data': "data:image/png;base64," + b64encode(f.read()), 'is-path': True}))
            else:
                self.finish(dumps({'data': res[0], 'is-path': False}))
        else:
            GW.submit_job(body['dataset-name'], body['function-name'], body['query'])
            self.set_status(202)
            self.finish()


class _DocumentationHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, *args):
        index = str(args[0]).strip()
        if not index:
            index = "index.html"

        self.set_status(200)
        self.render("%s/web/docs/_build/html/%s" % (get_static_path(), index))


class GatewayWebWrapper(Application):
    """
    Web wrapper to enable web access to the Gateway Python API.
    """

    def __init__(self, gateway):
        global GW
        GW = gateway

        settings = {
            r'static_path': r"%s/web/static" % get_static_path(),
            r'static_url_prefix': r'/static/',
        }

        routes = [
            (r"/docs/_static/(.*)", StaticFileHandler, {"path": "%s/web/docs/_build/html/_static" % get_static_path()}),
            (r"/fonts/(.*)", StaticFileHandler, {"path": "%s/web/static" % get_static_path()}),
            (r'/docs/(.*)', _DocumentationHandler),
        ]

        if isinstance(gateway, PyBDAEScientist):
            routes += [
                (r'/', _RootHandler),
                (r'/get_registered_datasets', _RegisteredDatasetHandler),
                (r'/get_operations/(.*)', _OperationsHandler),
                (r'/job', _JobHandler),
            ]

        if isinstance(gateway, PyBDAEManager):
            routes += [
                (r'/create', _CreateDatasetHandler),
                (r'/delete', _DeleteDatasetHandler),
                (r'/update', _UpdateDatasetHandler)
            ]

        if isinstance(gateway, PyBDAEAdmin):
            routes += [
                # TODO: add monitor apis
            ]

        Application.__init__(self, routes, **settings)

    def start(self, port, hostname='localhost'):
        """
        Method to start local or remote documentation and admin frontend.

        :param port: Port number of the local documentation and admin frontend
        :type port: int
        :param hostname (optional): default value is 'localhost'
        :type hostname: str
        """

        server = HTTPServer(self)
        server.listen(address=hostname, port=port)
        print "*** Running on localhost:%d" % port
        IOLoop.current().start()
