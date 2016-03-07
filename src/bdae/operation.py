# Created by Steffen Karlsson on 03-01-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from enum import Enum


class Parallel:
    def __init__(self, *functions):
        self.functions = functions


class Sequential:
    def __init__(self, *functions):
        self.functions = functions


class OperationContext:
    class GhostType(Enum):
        ELEMENT = 0
        BLOCK = 1
        ROW = 2
        COLUMN = 3

    class TypeNotSupportedException(Exception):
        pass

    def __init__(self, fun_name, sequential_operations):
        if not isinstance(sequential_operations, Sequential):
            raise NotImplemented("Outer operations has to be sequential and a reduce function as last operation/")

        self.fun_name = fun_name
        self.operations = sequential_operations.functions
        self.ghost_type = None
        self.ghost_num = 0
        self.num_args = 1
        self.delimiter = ','

    def with_ghost(self, ghost_num, ghost_type):
        # Halo Lines

        if not isinstance(ghost_type, OperationContext.GhostType):
            raise OperationContext.TypeNotSupportedException()

        self.ghost_type = ghost_type
        self.ghost_num = ghost_num
        return self

    def with_multiple_arguments(self, num_args, delimiter=','):
        self.num_args = num_args
        self.delimiter = delimiter
        return self

    def needs_ghost(self):
        return self.ghost_num > 0
