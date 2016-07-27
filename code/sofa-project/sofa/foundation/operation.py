# Created by Steffen Karlsson on 03-01-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from re import finditer
from base64 import b64encode
from simplejson import dumps


class ExpectedReturnType(object):
    Text, Number, Image, NumpyArray = range(4)

    types = {
        Text: 'txt',
        Number: 'num',
        Image: 'img',
        NumpyArray: 'numpy'
    }

    representation = {
        Text: lambda s: str(s),
        Number: lambda d: d,
        Image: lambda i: ExpectedReturnType._img_representation(i),
        NumpyArray: lambda a: dumps(a.tolist())
    }

    @staticmethod
    def _img_representation(i):
        with open(i, "rb") as f:
            return 'data:image/png;base64,' + b64encode(f.read())

    @staticmethod
    def as_string(return_type):
        return ExpectedReturnType.types[return_type]

    @staticmethod
    def get_representation(return_type, data):
        return ExpectedReturnType.representation[return_type](data)


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
            functions = [Sequential(*_crawl_syntax(context, _strip_operators(tail), [], seq_start,
                                                   seq_end, par_start, par_end))] + functions
            continue

        if tail.startswith(par_start) or tail.endswith(par_end):
            functions = [Parallel(*_crawl_syntax(context, _strip_operators(tail), [], seq_start,
                                                 seq_end, par_start, par_end))] + functions
            continue

        tail = tail.strip()
        function = context.verify_function(tail)
        if not function:
            raise Exception("Function %s is not valid compared to rules in verify_function" % function)

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
        self.ghost_count = (1, 1)
        self.delimiter = ','
        self.send_left = False
        self.send_right = False
        self.use_cyclic = False
        self.post_process = None
        self.return_type = ExpectedReturnType.Text
        self.num_arguments = 1
        self.supply_meta_data_arg = False

    def with_initial_ghosts(self, ghost_count=(1, 1), use_cyclic=False):
        is_tuple = isinstance(ghost_count, tuple)
        if is_tuple and len(ghost_count) != 2:
            raise Exception("Two counts (left, right) is required if ghost count is specified as a tuple, "
                            "otherwise specify as an int for symmetric ghosts")

        # Halo Lines
        self.ghost_count = ghost_count
        self.send_left = ghost_count[0] != 0 if is_tuple else True
        self.send_right = ghost_count[1] != 0 if is_tuple else True
        self.use_cyclic = use_cyclic
        return self

    def with_expected_return_type(self, return_type):
        self.return_type = return_type
        return self

    def with_post_processing(self, fun_post_process_step):
        self.post_process = fun_post_process_step
        return self

    def with_multiple_arguments(self, num_arguments):
        self.num_arguments = num_arguments
        return self

    def with_meta_data(self):
        self.supply_meta_data_arg = True
        return self

    def get_num_arguments(self):
        return self.num_arguments

    def get_ghost_count_left(self):
        return self.__get_ghost(0)

    def get_ghost_count_right(self):
        return self.__get_ghost(1)

    def __get_ghost(self, index):
        return self.ghost_count[index] if isinstance(self.ghost_count, tuple) else self.ghost_count

    def needs_ghost(self):
        return self.ghost_count > 0 and (self.send_left or self.send_right)

    def needs_both_ghosts(self):
        return self.send_right and self.send_left

    def has_post_processing_step(self):
        return self.post_process is not None

    def execute_post_process(self, args):
        return self.post_process(args)

    def get_functions(self):
        return list(self.functions)

    def requires_meta_data(self):
        return self.supply_meta_data_arg

    def get_return_type(self):
        return ExpectedReturnType.as_string(self.return_type)

    def get_data_return_representation(self, data):
        return ExpectedReturnType.get_representation(self.return_type, data)
