# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: libbdaeadmin
"""

from abc import abstractmethod, ABCMeta
from os import path
from ujson import dumps as udumps

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, asynchronous, StaticFileHandler

from bdae.utils import verify_error
from bdae.gateway import api as gateway_api
import bdae

ADMIN = None
API = None


def get_path():
    return path.dirname(path.abspath(bdae.__file__))


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


class RegisterDatasetHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    def compute_etag(self):
        return None

    @asynchronous
    def get(self):
        datasets = ADMIN.get_implemented_datasets()

        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(udumps(dict() if datasets is None else datasets))


class FunctionsHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, dataset_name, functions_type):
        functions = None

        if functions_type == 'operations':
            functions = API.get_dataset_operations(dataset_name)

        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(udumps(list() if functions is None else functions))


class SubmitJobHandler(RequestHandler):
    @asynchronous
    def get(self, dataset_name, function_name, query):
        res = API.submit_job(dataset_name, function_name, query)
        verify_error(res)

        self.set_status(res)
        self.finish()


TORNADO_SETTINGS = {
    r'static_path': r"%s/web/static" % get_path(),
    r'static_url_prefix': r'/static/',
}

TORNADO_ROUTES = [
    (r'/', RootHandler),
    (r'/register_implemented_datasets', RegisterDatasetHandler),
    (r'/get_functions/(.*)/(.*)', FunctionsHandler),
    (r'/submit/(.*)/(.*)/(.*)', SubmitJobHandler),
    (r"/docs/_static/(.*)", StaticFileHandler, {"path": "%s/web/docs/_build/html/_static" % get_path()}),
    (r"/fonts/(.*)", StaticFileHandler, {"path": "%s/web/static" % get_path()}),
    (r'/docs/(.*)', DocumentationHandler),
]


class AbsPyAdminGateway(Application):
    """
    Abstract class to override in order to implement a administrator gateway to the framework
    """

    __metaclass__ = ABCMeta

    def __init__(self, gateway_uri):
        super(AbsPyAdminGateway, self).__init__()
        self.__api = gateway_api(gateway_uri)

    def create_dataset(self, name, dataset_type):
        """
        Method to create a new dataset based on a name and a class reference, e.g. mypackage.myfile.MyDatasetClass

        :param name: Name of the dataset
        :type name: str
        :param dataset_type: Reference name of the dataset to be created
        :type dataset_type: str
        :raises DatasetAlreadyExistsException: If the name of the dataset already exists
        """
        verify_error(self.__api.create(name, dataset_type),
                     "Dataset with name: %s, already exists" % name)

    def append_to_dataset(self, name, url):
        """
        Method to append data from a url to an existing dataset created by :func:`create_dataset`.

        :param name: Name of the dataset
        :type name: str
        :param url: The path from where the framework gateway needs to download the data
        :type url: str
        :raises DatasetNotExistsException: If the dataset isn't already created by :func:`create_dataset`
        """

        verify_error(self.__api.append(name, url),
                     "Dataset with name: %s, doesn't exists" % name)

    @abstractmethod
    def get_implemented_datasets(self):
        """
        Abstract method to be overriden to return a dictionary of name, class reference combinations.

        Example:

        .. code-block:: python

            return {"my dataset name": "mypackage.myfile.MyDatasetClass"}

        :rtype: dict
        """
        pass

    def start_web(self, port, hostname='localhost'):
        """
        Method to start local or remote documentation and admin frontend.

        :param port: Port number of the local documentation and admin frontend
        :type port: int
        :param hostname (optional): default value is 'localhost'
        :type hostname: str
        """
        global ADMIN, API
        ADMIN = self
        API = self.__api

        Application.__init__(self, TORNADO_ROUTES, **TORNADO_SETTINGS)
        server = HTTPServer(self)
        server.listen(address=hostname, port=port)
        print "*** Running on localhost:%d" % port
        IOLoop.current().start()
