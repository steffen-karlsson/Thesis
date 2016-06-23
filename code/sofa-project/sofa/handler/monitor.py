# Created by Steffen Karlsson on 02-21-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from logging import error, info
from subprocess import Popen, PIPE

from Pyro4.errors import CommunicationError

from sofa.foundation.scheduler import BackgroundDaemonScheduler

from sofa.handler.api import _StorageToMonitorApi


class MonitorHandler(object):
    def __init__(self, config, others):
        self.__config = config

        if 'storage' in others:
            self.__storage_nodes = [(address, storage_uri, _StorageToMonitorApi(storage_uri))
                                    for storage_uri, address in others['storage']]
        else:
            self.__storage_nodes = []

        self.__heartbeat_scheduler = None
        self.__potential_dead_nodes = {}
        self.setup_schedulers()

    def setup_schedulers(self):
        self.__heartbeat_scheduler = BackgroundDaemonScheduler()
        self.__heartbeat_scheduler.add_job(self.__scheduler_heartbeat, 'interval',
                                           seconds=self.__config.heartbeat_scheduler_delay)
        self.__heartbeat_scheduler.start()

    def __handle_potential_dead_node(self, address, uri, node):
        scheduler, count = self.__potential_dead_nodes[uri]

        def __remove_scheduler():
            scheduler.shutdown()
            del self.__potential_dead_nodes[uri]

        if count > self.__config.num_heartbeat_retries:
            # Kill the node
            __remove_scheduler()
            self.__handle_dead_node(address, uri)

        try:
            node.heartbeat()
            # Alive anyway
            __remove_scheduler()
        except CommunicationError:
            # Still not alive
            self.__potential_dead_nodes[uri] = (scheduler, count + 1)
            pass

    def __handle_dead_node(self, address, uri):
        if not self.__config.live_software_reboot:
            error("%s is dead and live reboot isn't enabled" % uri)
            return

        # Live reboot
        index = uri.split(":")[-1]
        command = "python %s/boot.py %s \"%s\" storage" \
                  % (self.__config.project_path, index, self.__config.encode())
        Popen(["ssh", address.split(':')[0], command],
              shell=False,
              stdout=PIPE,
              stderr=PIPE)
        info("%s was dead and now reboot" % uri)

    def __scheduler_heartbeat(self):
        try:
            for address, uri, node in self.__storage_nodes:
                node.heartbeat()
                info("%s is alive" % uri)
        except CommunicationError:
            if not uri in self.__potential_dead_nodes:
                dead_scheduler = BackgroundDaemonScheduler()
                dead_scheduler.add_job(self.__handle_potential_dead_node, 'interval',
                                       seconds=0.200, args=[address, uri, node])
                self.__potential_dead_nodes[uri] = (dead_scheduler, 1)
                dead_scheduler.start()
                self.__heartbeat_scheduler.shutdown()
