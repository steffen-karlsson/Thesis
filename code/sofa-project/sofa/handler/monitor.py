# Created by Steffen Karlsson on 02-21-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from apscheduler.schedulers.background import BackgroundScheduler
from Pyro4.errors import CommunicationError

from sofa.handler.api import _StorageToMonitorApi


class MonitorHandler(object):
    def __init__(self, config, storage_uris):
        self.__config = config
        self.__storage_nodes = [(storage_uri, _StorageToMonitorApi(storage_uri)) for storage_uri in storage_uris]
        self.__heartbeat_scheduler = None

        self.setup_schedulers()

    def setup_schedulers(self):
        self.__heartbeat_scheduler = BackgroundScheduler()
        self.__heartbeat_scheduler.add_job(self.__scheduler_heartbeat, 'interval',
                                           seconds=self.__config.heartbeat_scheduler_delay)
        self.__heartbeat_scheduler.start()

    def __scheduler_heartbeat(self):
        try:
            for uri, node in self.__storage_nodes:
                node.heartbeat()
                print "%s is alive" % uri
        except CommunicationError as e:
            print "%s is dead" % uri
