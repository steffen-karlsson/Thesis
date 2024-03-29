# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from logging import error, info
from sys import argv
from signal import signal, SIGTERM, SIGINT

from Pyro4 import Daemon, config as pyro_config
from Pyro4.naming import locateNS, startNSloop

from sofa.handler.gateway import GatewayHandler
from sofa.handler.storage import StorageHandler
from sofa.handler.monitor import MonitorHandler
from sofa.config import validate_configuration, _InvalidConfigurationFile
from sofa.config.parser import Configuration

REGISTRY_NAME = None
DAEMON = None
NS = None

pyro_config.SERVERTYPE = "thread"
pyro_config.THREADING2 = True
pyro_config.SERIALIZER = 'pickle'
pyro_config.SERIALIZERS_ACCEPTED.add('pickle')
pyro_config.COMPRESSION = True


def _handle_kill_signal(signal, frame):
    NS.remove(REGISTRY_NAME)
    DAEMON.close()
    exit(1)


def start_nameserver(hostname='localhost', port=9090):
    startNSloop(host=hostname, port=port)


if __name__ == "__main__":
    node_types = argv[3:]
    node_type = node_types[0]

    cfg_file = argv[2]
    index = int(argv[1])

    try:
        config = validate_configuration(cfg_file, index, node_types)
    except _InvalidConfigurationFile, e:
        try:
            # Could be json from a live software boot
            config = Configuration.decode(cfg_file, index)
        except ValueError:
            raise _InvalidConfigurationFile(e.message)

    if config is None:
        error("Unable to start %s without configuration" % node_type)
        exit(1)

    NS = locateNS(host=config.name_server[0], port=config.name_server[1])

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

    DAEMON = Daemon(port=config.port, host=config.hostname)

    uri = DAEMON.register(instance(config, config.others))
    REGISTRY_NAME = config.node
    NS.register(REGISTRY_NAME, uri)

    signal(SIGTERM, _handle_kill_signal)
    signal(SIGINT, _handle_kill_signal)

    info("%s ready at %s with registry: %s" % (node_type, str(uri), config.node))
    DAEMON.requestLoop()
