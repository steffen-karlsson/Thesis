# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from logging import error, info
from sys import argv
from signal import signal, SIGTERM, SIGINT

from Pyro4 import Daemon, locateNS

from bdos.gateway import handler as gateway_handler
from bdos.storage import handler as storage_handler
from bdos.monitor import handler as monitor_handler
from config import validate_configuration

REGISTRY_NAME = None
NS = locateNS()


def _handle_kill_signal(signal, frame):
    NS.remove(REGISTRY_NAME)
    exit(1)


if __name__ == "__main__":
    node_type = argv[1]
    index = int(argv[3])

    config = validate_configuration(node_type)

    if config.node is None:
        error("Unable to start %s without configuration" % node_type)
        exit(1)

    instance = None
    if config.node.type == "gateway":
        instance = gateway_handler
    if config.node.type == "storage":
        instance = storage_handler
    if config.node.type == "monitor":
        instance = monitor_handler

    if instance is None:
        error("Node with type: %s is not supported" % config.node.type)
        exit(1)

    REGISTRY_NAME = "%s-%d" % (config.node.ns_registry_name, index)
    daemon = Daemon(port=config.node.get_port(index))

    # TODO: define list other storage nodes instead of None
    uri = daemon.register(instance(config.block_size, None))
    NS.register(REGISTRY_NAME, uri)

    signal(SIGTERM, _handle_kill_signal)
    signal(SIGINT, _handle_kill_signal)

    info("%s ready at %s with registry: %s" % (node_type, str(uri), REGISTRY_NAME))
    daemon.requestLoop()
