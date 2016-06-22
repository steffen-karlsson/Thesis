# Created by Steffen Karlsson on 05-30-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from functools import wraps
from math import floor

from sofa.delegation import is_function_delegation, is_delegation_handler


def find_responsible(identifier, key_space):
    return int(floor(identifier / key_space))


def with_responsible_dispatch(func):
    @wraps(func)
    def dispatch_wrapper(*args):
        context = args[0]
        fd = args[1]

        if is_delegation_handler(context) and is_function_delegation(fd):
            # Check whether its self who is responsible
            responsible_idx = find_responsible(fd['identifier'], context.get_key_space())

            # Offset by replication index too
            responsible_idx = (responsible_idx + fd['replica-index']) \
                              % context.get_num_storage_nodes(including_self=True)

            if context.me() == responsible_idx:
                # My self to handle the data
                res = func(*args)
                return res

            responsible = context.get_responsible(responsible_idx)
            return getattr(responsible, func.__name__)(*args[1:])  # Not include self reference

    return dispatch_wrapper
