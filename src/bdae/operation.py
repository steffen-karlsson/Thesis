# Created by Steffen Karlsson on 03-01-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from enum import Enum
from re import finditer
from inspect import isgeneratorfunction


def _is_alpha(s):
    return str(s).strip().replace('_', '').isalpha()


def _strip(s):
    return s.strip()[1:-1]


def _balanced_split(syntax, seq_start, seq_end, par_start, par_end):
    indices = [x.start() for x in finditer(',', syntax)]
    idx = -1
    tail = ""
    head = ""

    def _equal_count(s):
        return s.count(seq_start) == s.count(seq_end) and s.count(par_start) == s.count(par_end)

    while not tail or not (_equal_count(head) or _equal_count(tail)):
        split = indices[idx]
        tail = syntax[split + 1:]
        head = syntax[:split]
        idx -= 1

    return head, tail


def _crawl_syntax(function_map, syntax, functions, seq_start, seq_end, par_start, par_end):
    while syntax:
        try:
            syntax, tail = _balanced_split(syntax, seq_start, seq_end, par_start, par_end)
        except IndexError:
            tail = syntax
            syntax = ""

        if tail.startswith(seq_start) or tail.endswith(seq_end):
            functions = [Sequential(*_crawl_syntax(function_map, _strip(tail), [], seq_start,
                                                   seq_end, par_start, par_end))] + functions
            continue

        if tail.startswith(par_start) or tail.endswith(par_end):
            functions = [Parallel(*_crawl_syntax(function_map, _strip(tail), [], seq_start,
                                                 seq_end, par_start, par_end))] + functions
            continue

        tail = tail.strip()
        if not _is_alpha(tail):
            raise Exception("Unknown syntax: " + syntax)

        if tail not in function_map:
            raise Exception("Function %s not defined in get_map_functions nor get_reduce_functions." % tail)

        functions = [function_map[tail]] + functions

    return functions


class Parallel:
    def __init__(self, *functions):
        self.functions = functions


class Sequential:
    def __init__(self, *functions):
        self.functions = functions


class OperationContext:
    class GhostType(Enum):
        ENTRY = 1

    class TypeNotSupportedException(Exception):
        pass

    @staticmethod
    def by(dataset_context, fun_name, syntax, sequential_operator=('[', ']'), parallel_operator=('{', '}')):
        if not isinstance(syntax, str):
            raise Exception("Synatx has to be of type string")

        if not all(sequential_operator) or len(sequential_operator) != 2:
            raise Exception("Must have two and only two sequential operators, begin and end")

        if not all(parallel_operator) or len(parallel_operator) != 2:
            raise Exception("Must have two and only two parallel operators, begin and end")

        if len(set(list(sequential_operator) + list(parallel_operator))) != 4:
            raise Exception("Operators has to be unique")

        syntax = syntax.strip()
        seq_start = sequential_operator[0]
        seq_end = sequential_operator[1]
        par_start = parallel_operator[0]
        par_end = parallel_operator[1]

        if not syntax.startswith(seq_start) or not syntax.endswith(seq_end):
            raise Exception("Synatx has start with %s and end with %s" % (seq_start, seq_end))

        function_map = {func.func_name: func for func
                        in dataset_context.get_map_functions() + dataset_context.get_reduce_functions()}

        syntax, rfun = _strip(syntax).rsplit(",", 1)
        rfun = rfun.strip()
        if rfun not in function_map:
            raise Exception("Element in the %s ... %s has to be a reduce function" % (seq_start, seq_end))

        functions = _crawl_syntax(function_map, syntax, [function_map[rfun]], seq_start, seq_end, par_start, par_end)
        return OperationContext(dataset_context, fun_name, Sequential(*functions))

    def __init__(self, dataset_context, fun_name, sequential_operations):
        if not isinstance(sequential_operations, Sequential):
            raise Exception("Outer operations has to be sequential and a reduce function as last operation")

        if sequential_operations.functions[-1] not in dataset_context.get_reduce_functions():
            raise Exception("Last operation has to be a reduction")

        for map_fun in dataset_context.get_map_functions():
            if not isgeneratorfunction(map_fun):
                raise Exception("%s is not an generator i.e. yields" % map_fun.func_name)

        self.fun_name = fun_name
        self.operations = sequential_operations.functions
        self.ghost_type = None
        self.ghost_count = 0
        self.num_args = 1
        self.delimiter = ','
        self.ghost_left = False
        self.ghost_right = False
        self.use_cyclic = False

    def with_ghost(self, ghost_count, ghost_type, use_ghost_left, use_ghost_right, use_cyclic=False):
        # Halo Lines

        if not isinstance(ghost_type, OperationContext.GhostType):
            raise OperationContext.TypeNotSupportedException()

        self.ghost_type = ghost_type
        self.ghost_count = ghost_count
        self.ghost_left = use_ghost_left
        self.ghost_right = use_ghost_right
        self.use_cyclic = use_cyclic
        return self

    def with_multiple_arguments(self, num_args, delimiter=','):
        self.num_args = num_args
        self.delimiter = delimiter
        return self

    def needs_ghost(self):
        return self.ghost_count > 0 and (self.ghost_left or self.ghost_right)

    def has_multiple_args(self):
        return self.num_args > 1

    def get_operations(self):
        return list(self.operations)
