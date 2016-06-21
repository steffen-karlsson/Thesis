# Created by Steffen Karlsson on 06-21-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from functools import wraps

from sofa.delegation import is_delegation_handler, is_function_delegation


def __generate_queue(root_idx, replication_factor, max_nodes, include_self=False):
    if max_nodes == 1:
        return []

    q = [(idx + (root_idx - 0)) % max_nodes for idx in xrange(1, replication_factor)]
    if include_self:
        q += [root_idx]

    return q


def with_forward_count(func):
    @wraps(func)
    def forward_count_wrapper(*args):
        context = args[0]

        if is_delegation_handler(context):
            context.increment_job_count()
            res = func(*args)
            context.decrease_job_count(1)
            return res

    return forward_count_wrapper


def with_forward_queue(func):
    @wraps(func)
    def forward_queue_wrapper(*args):
        context = args[0]
        fd = args[1]

        if is_delegation_handler(context) and is_function_delegation(fd):
            queue = fd['queue']

            if not fd['is-root']:
                fd['is-root'] = True

            if not fd['replication-factor']:
                fd['replication-factor'] = context.get_replication_factor(fd['identifier'])

            def __local_run():
                return func(*args)

            def __forward_job(responsible_idx, forward_arguments):
                responsible = context.get_responsible(responsible_idx)
                return getattr(responsible, func.__name__)(*forward_arguments[1:])

            if fd['is-root']:
                if fd['replication-factor'] == 1:
                    # No other replicas than this, do the job
                    return __local_run()
                else:
                    # Generate forward queue
                    queue = __generate_queue(context.me(), fd['replication-factor'],
                                             context.get_num_storage_nodes(including_self=True),
                                             include_self=True)

            # Check own count before passing on the job
            if context.get_current_job_count() < fd['min-work-count']:
                # Do the job, not enough work to do
                return __local_run()
            else:
                if queue:
                    # Pass the job to the next in the queue
                    responsible_idx = queue.pop(0)
                    return __forward_job(responsible_idx, [queue] + args[2:])
                else:
                    # The queue is empty, have to do the job
                    return __local_run()

    return forward_queue_wrapper


def with_required_queue(func):
    @wraps(func)
    def required_wrapper(*args):
        context = args[0]
        fd = args[1]

        if is_delegation_handler(context) and is_function_delegation(fd):
            res = func(*args)

            # TODO: eventually pipeline the data transfer, instead of root sending all

            if fd['is-root']:
                # Distribute to the other replicas
                num_storage_nodes = context.get_num_storage_nodes(including_self=True)

                # Implementing simple store and forward method
                for replication_index in xrange(1, fd['replication-factor']):
                    # Update state
                    fd['replica-index'] = replication_index
                    fd['is-root'] = False

                    responsible_idx = (context.me() + replication_index) % num_storage_nodes

                    # Offset by replication index too
                    responsible = context.get_responsible(responsible_idx)
                    res = getattr(responsible, func.__name__)(*args[1:])

            # TODO: eventually sum up the results and check them one by one
            return res

    return required_wrapper
