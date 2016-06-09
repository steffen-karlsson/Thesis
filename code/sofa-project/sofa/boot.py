# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from logging import error, info
from sys import argv
from signal import signal, SIGTERM, SIGINT

from Pyro4 import Daemon, locateNS, config as pyro_config

from sofa.handler.gateway import GatewayHandler
from sofa.handler.storage import StorageHandler
from sofa.handler.monitor import MonitorHandler
from sofa.config import validate_configuration

REGISTRY_NAME = None
DAEMON = None
NS = locateNS()

def _handle_kill_signal(signal, frame):
    NS.remove(REGISTRY_NAME)
    DAEMON.close()
    exit(1)


if __name__ == "__main__":
    pyro_config.SERVERTYPE = "thread"
    pyro_config.THREADING2 = True

    node_types = argv[3:]

    cfg_file = argv[2]
    config = validate_configuration(cfg_file, int(argv[1]), node_types)
    node_type = node_types[0]

    if config is None:
        error("Unable to start %s without configuration" % node_type)
        exit(1)

    instance = None
    if node_type == "gateway":
        instance = GatewayHandler
    if node_type == "storage":
        instance = StorageHandler
    if node_type == "monitor":
        instance = MonitorHandler

    if instance is None:
        error("Node with type: %s is not supported" % config.node.type)
        exit(1)

    DAEMON = Daemon(port=config.port)

    uri = DAEMON.register(instance(config, config.others))
    REGISTRY_NAME = config.node
    NS.register(REGISTRY_NAME, uri)

    signal(SIGTERM, _handle_kill_signal)
    signal(SIGINT, _handle_kill_signal)

    info("%s ready at %s with registry: %s" % (node_type, str(uri), config.node))
    DAEMON.requestLoop()
