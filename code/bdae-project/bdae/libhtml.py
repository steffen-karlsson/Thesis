# Created by Steffen Karlsson on 06-02-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from ujson import dumps as udumps, loads as uloads
from argparse import ArgumentParser

from Pyro4.errors import NamingError

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from tornado.web import RequestHandler, asynchronous, Application

from bdae.api import GatewayScientistApi

API = None
InstanceName = None


def check_instance(handler, instance_name):
    if instance_name != InstanceName:
        handler.send_error(401)
        return False

    return True


def finalize_data(handler, data):
    if data is None or not data:
        handler.set_status(204)
        handler.finish()
    else:
        handler.set_status(200)
        handler.finish(udumps(data))


class _DatasetHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, instance_name):
        if check_instance(self, instance_name):
            datasets = API.get_datasets()
            self.set_header('Content-Type', 'application/json')
            finalize_data(self, datasets)


class _CollectionHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, instance_name):
        if check_instance(self, instance_name):
            # TODO: Implement collection handler
            pass


class _SubmittedJobsHandler(RequestHandler):
    SUPPORTED_METHODS = {'GET'}

    @asynchronous
    def get(self, instance_name):
        if check_instance(self, instance_name):
            jobs = API.get_submitted_jobs()
            self.set_header('Content-Type', 'application/json')
            finalize_data(self, jobs)


class _SubmitNewJobHandler(RequestHandler):
    SUPPORTED_METHODS = {'POST'}

    def post(self, *args, **kwargs):
        parameters = uloads(self.request.body)
        if "dataset_name" in parameters and "operation_name" in parameters and "query" in parameters:
            self.set_status(201)
            self.finish()

            API.submit_job(parameters['dataset_name'], parameters["operation_name"], parameters["query"])
        else:
            self.set_status(400)
            self.finish()


class _InitializeHandler(RequestHandler):
    SUPPORTED_METHODS = {'PUT'}

    @asynchronous
    def put(self, *args, **kwargs):
        self.get_arguments('')
        instance_name = self.get_argument('instance-name', None)
        identifier = self.get_argument('identifier', None)

        try:
            global API, InstanceName
            API = GatewayScientistApi(str("sofa:%s:gateway:%s" % (instance_name, identifier)))
            InstanceName = instance_name

            self.set_status(200)
            self.finish()
        except NamingError:
            self.send_error(503)


class APIServer(Application):
    def __init__(self):
        routes = [
            (r'/api/initialize', _InitializeHandler),
            (r'/api/(\w*)/get_datasets', _DatasetHandler),
            (r'/api/(\w*)/get_collections', _CollectionHandler),
            (r'/api/(\w*)/get_submitted_jobs', _SubmittedJobsHandler),
            (r'/api/(\w*)/submit_new_job', _SubmitNewJobHandler)
        ]

        Application.__init__(self, routes)

    def start(self, ip, port):
        server = HTTPServer(self)
        server.listen(address=ip, port=port)
        print "*** Running on %s:%d" % (ip, port)
        IOLoop.current().start()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-i", help="Ip address of instance", default="0.0.0.0", type=str)
    parser.add_argument("-p", help="Port number of instance", default=9990, type=int)
    args = parser.parse_args()

    APIServer().start(args.i, args.p)
