# Created by Steffen Karlsson on 06-21-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta, abstractmethod


class FunctionDelegation(dict):
    def __init__(self, identifier, **kwargs):
        super(FunctionDelegation, self).__init__(**kwargs)
        self['identifier'] = identifier
        self['type'] = 'fd'
        self['replica-index'] = 0

    def as_dispatch_delegation(self):
        return self

    def as_forward_queue_delegation(self, queue, min_work_count, replication_factor):
        self['is-root'] = None
        self['queue'] = queue
        self['min-work-count'] = min_work_count
        self['replication-factor'] = replication_factor
        return self

    def as_required_queue_delegation(self, queue, replication_factor):
        self['is-root'] = None
        self['queue'] = queue
        self['replication-factor'] = replication_factor
        return self


class DelegationHandler:
    __metaclass__ = ABCMeta

    def __init__(self, my_idx, key_space_size):
        self.__my_idx = my_idx
        self.__key_space_size = key_space_size
        self.__cjc = 0

    def setup(self, my_idx, key_space_size):
        self.__key_space_size = key_space_size
        self.__my_idx = my_idx

    @abstractmethod
    def get_responsible(self, index):
        pass

    @abstractmethod
    def get_num_storage_nodes(self, including_self=False):
        pass

    @abstractmethod
    def get_replication_factor(self, identifier):
        pass

    def me(self):
        return self.__my_idx

    def get_key_space(self):
        return self.__key_space_size

    def get_current_job_count(self):
        return self.__cjc

    def increase_job_count(self, count):
        self.__cjc += count

    def increment_job_count(self):
        self.increase_job_count(1)

    def decrease_job_count(self, count):
        self.__cjc -= count


def is_function_delegation(arg):
    if not isinstance(arg, dict):
        raise AttributeError("First arg has to be of type FunctionDelegation")

    if 'type' not in arg or arg['type'] != 'fd':
        raise AttributeError("First arg has to be of type FunctionDelegation")

    return True


def is_delegation_handler(arg):
    if not isinstance(arg, DelegationHandler):
        raise AttributeError("self has to be of type DelegationHandler")

    return True
