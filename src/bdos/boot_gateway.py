# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from Pyro4 import Daemon
from config import validate_configuration
from logging import error, info
from sys import argv, path
from __init__ import NS
from utils import import_class
from signal import signal, SIGTERM, SIGINT

REGISTRY_NAME = None

def _handle_kill_signal(signal, frame):
    NS.remove(REGISTRY_NAME)
    exit(1)

if __name__ == "__main__":
    config = validate_configuration()
    index = int(argv[2])

    if config.gateway is None:
        error("Unable to start gateway without configuration")
        exit(1)

    file_name = "%s%s" % (config.project_path, config.gateway.file)
    path.append(config.project_path)

    cls = str("%s/%s" % (config.gateway.file.replace(".py", ""), config.gateway.name)).replace("/", ".")
    instance = import_class(cls)

    REGISTRY_NAME = "%s-%d" % (config.gateway.ns_registry_name, index)
    daemon = Daemon(port=config.gateway.get_port(index))
    uri = daemon.register(instance)
    NS.register(REGISTRY_NAME, uri)

    signal(SIGTERM, _handle_kill_signal)
    signal(SIGINT, _handle_kill_signal)

    info("Gateway ready at %s with registry: %s" % (str(uri), REGISTRY_NAME))
    daemon.requestLoop()
