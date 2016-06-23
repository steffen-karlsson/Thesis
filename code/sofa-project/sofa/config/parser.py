# Created by Steffen Karlsson on 02-12-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

"""
.. module:: configparser
"""

from ConfigParser import SafeConfigParser
from logging import basicConfig, INFO, debug
from os.path import exists
from os import makedirs
from simplejson import loads, dumps
from base64 import b64encode, b64decode

DEFAULT_BLOCK_SIZE = 64
DEFAULT_PORT = 9090
DEFAULT_HEARTBEAT_DELAY = 5
DEFAULT_HEARTBEAT_RETRIES = 5
DEFAULT_KEYSPACE_SIZE = pow(2, 64)


class ParameterRequiredException(Exception):
    """
    Simple exception class to be thrown if a required parameter isn't present.
    """

    def __init__(self, message):
        super(ParameterRequiredException, self).__init__(message)


def parse_project_cfg(path, index, node_types):
    """
    Function to parse .cfg file defined by the parameter ``path``.

    Example:

    .. code-block:: cfg

        ##
        # SOFA Configuration
        #

        [general]
        project-path =
        log-file =
        keyspace-size =
        mount-point =
        instance-name =

        # Defined in seconds
        heartbeat-scheduler-delay =
        num-heartbeat-retries =
        enable-live-software-reboot =

        # Load balancing
        load-balancing-threshold =

        # Defined in megabytes
        block-size =

        ##
        # Configuration of the nodes
        # Available section types:
        #   * gateway, storage, monitor
        #
        # Supported parameters:
        #   * addresses - list of ip addresses and port pairs (= number of gateways started)
        #   * ns-registry-name - identifier at the nameserver
        #

        [gateway]
        addresses =

        [storage]
        addresses =

        [monitor]
        addresses =


    :param path: full path to the .cfg project configuration file
    :param node_type: The node type to parse: gateway, storage, monitor
    :type path: str
    :returns :class:`.Configuration`
    """

    config = SafeConfigParser(allow_no_value=True)
    config.read(path)

    global_config = Configuration()
    if not config.has_option("general", "project-path"):
        raise ParameterRequiredException("project-path in general is required")
    global_config.project_path = config.get("general", "project-path")

    if not config.has_option("general", "instance-name"):
        raise ParameterRequiredException("instance-name in general is required")
    instance_name = global_config.instance_name = config.get("general", "instance-name")

    if config.has_option("general", "mount-point"):
        global_config.mount_point = config.get("general", "mount-point")

    if not exists(global_config.mount_point):
        makedirs(global_config.mount_point)

    if config.has_option("general", "log-file"):
        basicConfig(filename=config.get("general", "log-file"), level=INFO)
        global_config.use_logging = True

    if config.has_option("general", "block-size"):
        global_config.block_size = config.getfloat("general", "block-size")

    if config.has_option("general", "heartbeat-scheduler-delay"):
        global_config.heartbeat_scheduler_delay = config.getint("general", "heartbeat-scheduler-delay")

    if config.has_option("general", "num-heartbeat-retries"):
        global_config.num_heartbeat_retries = config.getint("general", "num-heartbeat-retries")

    if config.has_option("general", "enable-live-software-reboot"):
        global_config.live_software_reboot = config.getboolean("general", "enable-live-software-reboot")

    if config.has_option("general", "keyspace-size"):
        global_config.keyspace_size = eval(config.get("general", "keyspace-size"))

    if config.has_option("general", "load-balancing-threshold"):
        global_config.load_balancing_threshold = config.getint("general", "load-balancing-threshold")

    for idx, node in enumerate(node_types):
        if config.has_section(node):
            if not config.has_option(node, "addresses"):
                raise ParameterRequiredException("addresses in %s is required" % node)

            addresses = config.get(node, "addresses").split(",")

            if idx == 0:
                global_config.node = "sofa:%s:%s:%d" % (instance_name, node, index)
                global_config.node_idx = index
                global_config.port = int(addresses[index].split(":")[1])

                if len(addresses) > 1:
                    others = [("sofa:%s:%s:%d" % (instance_name, node, i), address)
                              for i, address in enumerate(addresses)]
                    others.__delitem__(index)
                    global_config.others[node] = others
            else:
                global_config.others[node] = [("sofa:%s:%s:%d" % (instance_name, node, i), address)
                                              for i, address in enumerate(addresses)]
        else:
            if global_config.use_logging:
                debug("Starting system without %s" % node)

    return global_config


class Configuration:
    """
    Container class for configuration parameters defined in the .cfg project configuration file
    """

    def __init__(self):
        self.project_path = None
        self.instance_name = None
        self.use_logging = False
        self.block_size = DEFAULT_BLOCK_SIZE
        self.node = None
        self.node_idx = None
        self.others = {}
        self.keyspace_size = DEFAULT_KEYSPACE_SIZE
        self.port = DEFAULT_PORT
        self.heartbeat_scheduler_delay = DEFAULT_HEARTBEAT_DELAY
        self.num_heartbeat_retries = DEFAULT_HEARTBEAT_RETRIES
        self.live_software_reboot = False
        self.load_balancing_threshold = 1
        self.mount_point = "/mnt/sofa/"

    def get_mount_point(self):
        return self.mount_point if self.mount_point.endswith('/') else "%s/" % self.mount_point

    def encode(self):
        return b64encode(dumps(self.__dict__))

    @staticmethod
    def decode(json, index):
        json = loads(b64decode(json))
        config = Configuration()
        config.project_path = json['project_path']
        config.instance_name = json['instance_name']
        config.use_logging = json['use_logging']
        config.block_size = json['block_size']
        config.keyspace_size = json['keyspace_size']
        config.heartbeat_scheduler_delay = json['heartbeat_scheduler_delay']
        config.num_heartbeat_retries = json['num_heartbeat_retries']
        config.live_software_reboot = json['live_software_reboot']
        config.load_balancing_threshold = json['load_balancing_threshold']
        config.mount_point = json['mount_point']

        # Custom instantiation required for this instance
        storage_nodes = [tuple(storage) for storage in json['others']['storage']]
        me = storage_nodes.pop(index)

        config.node = me[0]
        config.node_idx = index
        config.port = int(me[1].split(":")[1])
        config.others = {'storage': storage_nodes}
        return config


if __name__ == "__main__":
    # Only used for test the parsing of .cfg file
    parse_project_cfg("../sofa.cfg", 0, ["gateway", "storage"])
