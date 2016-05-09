# Created by Steffen Karlsson on 03-01-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from re import finditer


def _strip_operators(s):
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


def _crawl_syntax(context, syntax, functions, seq_start, seq_end, par_start, par_end):
    while syntax:
        try:
            syntax, tail = _balanced_split(syntax, seq_start, seq_end, par_start, par_end)
        except IndexError:
            tail = syntax
            syntax = ""

        if tail.startswith(seq_start) or tail.endswith(seq_end):
            functions = [Sequential(*_crawl_syntax(context, _strip(tail), [], seq_start,
                                                   seq_end, par_start, par_end))] + functions
            continue

        if tail.startswith(par_start) or tail.endswith(par_end):
            functions = [Parallel(*_crawl_syntax(context, _strip(tail), [], seq_start,
                                                 seq_end, par_start, par_end))] + functions
            continue

        tail = tail.strip()
        function = context.verify_function(tail)
        if not function:
            raise Exception("Function %s is not valid compared to rules in verify_function" % tail)

        functions = [function] + functions

    return functions


class Parallel:
    def __init__(self, *functions):
        self.functions = functions


class Sequential:
    def __init__(self, *functions):
        self.functions = functions


class OperationContext:
    class TypeNotSupportedException(Exception):
        pass

    @staticmethod
    def by(context, fun_name, syntax, sequential_operator=('[', ']'), parallel_operator=('{', '}')):
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
            raise Exception("Syntax has start with %s and end with %s, i.e. be sequential" % (seq_start, seq_end))

        syntax, last_fun = _strip_operators(syntax).rsplit(",", 1)
        functions = _crawl_syntax(context, syntax, [context.verify_function(last_fun.strip())],
                                  seq_start, seq_end, par_start, par_end)
        return OperationContext(fun_name, Sequential(*functions))

    def __init__(self, fun_name, sequential_operations):
        if not isinstance(sequential_operations, Sequential):
            raise Exception("Outer operations has to be sequential")

        self.fun_name = fun_name
        self.functions = sequential_operations.functions
        self.ghost_count = 0
        self.num_args = 1
        self.delimiter = ','
        self.ghost_left = False
        self.ghost_right = False
        self.use_cyclic = False

    def with_initial_ghosts(self, ghost_count, use_ghost_left, use_ghost_right, use_cyclic=False):
        # Halo Lines
        self.ghost_count = ghost_count
        self.ghost_left = use_ghost_left
        self.ghost_right = use_ghost_right
        self.use_cyclic = use_cyclic
        return self

    def needs_ghost(self):
        return self.ghost_count > 0 and (self.ghost_left or self.ghost_right)

    def needs_both_ghosts(self):
        return self.ghost_right and self.ghost_left

    def has_multiple_args(self):
        return self.num_args > 1

    def get_functions(self):
        return list(self.functions)
