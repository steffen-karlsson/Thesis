# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from logging import error, info
from sys import argv
from signal import signal, SIGTERM, SIGINT

from Pyro4 import Daemon, locateNS

from bdae.gateway import handler as gateway_handler
from bdae.storage import handler as storage_handler
from bdae.monitor import handler as monitor_handler
from config import validate_configuration

REGISTRY_NAME = None
NS = locateNS()


def _handle_kill_signal(signal, frame):
    NS.remove(REGISTRY_NAME)
    exit(1)


if __name__ == "__main__":
    index = int(argv[1])
    node_types = argv[3:]

    config = validate_configuration(index, node_types)
    node_type = node_types[index]

    if config is None:
        error("Unable to start %s without configuration" % node_type)
        exit(1)

    instance = None
    if node_type == "gateway":
        instance = gateway_handler
    if node_type == "storage":
        instance = storage_handler
    if node_type == "monitor":
        instance = monitor_handler

    if instance is None:
        error("Node with type: %s is not supported" % config.node.type)
        exit(1)

    daemon = Daemon(port=config.port)

    uri = daemon.register(instance(config.block_size, config.others))
    NS.register(config.node, uri)

    signal(SIGTERM, _handle_kill_signal)
    signal(SIGINT, _handle_kill_signal)

    info("%s ready at %s with registry: %s" % (node_type, str(uri), config.node))
    daemon.requestLoop()
