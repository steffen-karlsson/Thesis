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
        ENTRY = 1

    class TypeNotSupportedException(Exception):
        pass

    def __init__(self, fun_name, sequential_operations):
        if not isinstance(sequential_operations, Sequential):
            raise NotImplemented("Outer operations has to be sequential and a reduce function as last operation/")

        self.fun_name = fun_name
        self.operations = sequential_operations.functions
        self.ghost_type = None
        self.ghost_count = 0
        self.num_args = 1
        self.delimiter = ','
        self.ghost_left = False
        self.ghost_right = False
        self.use_overflow = False

    def with_ghost(self, ghost_count, ghost_type, use_ghost_left, use_ghost_right, use_overflow=False):
        # Halo Lines

        if not isinstance(ghost_type, OperationContext.GhostType):
            raise OperationContext.TypeNotSupportedException()

        self.ghost_type = ghost_type
        self.ghost_count = ghost_count
        self.ghost_left = use_ghost_left
        self.ghost_right = use_ghost_right
        self.use_overflow = use_overflow
        return self

    def with_multiple_arguments(self, num_args, delimiter=','):
        self.num_args = num_args
        self.delimiter = delimiter
        return self

    def needs_ghost(self):
        return self.ghost_count > 0 and (self.ghost_left or self.ghost_right)

    def has_multiple_args(self):
        return self.num_args > 1
