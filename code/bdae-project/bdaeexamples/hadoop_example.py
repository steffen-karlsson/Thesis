# Created by Steffen Karlsson on 06-13-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sofa.foundation.base import load_data_by_path
from bdae.templates.text_dataset import TextDataByLine
from sofa.foundation.operation import OperationContext
from numpy import array, zeros

LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']


class LogEventParserData(TextDataByLine):
    def preprocess(self, data_ref):
        return load_data_by_path(data_ref)

    def get_operations(self):
        return [OperationContext.by(self, 'count logs', '[log_mapper, log_reducer]')
                    .with_post_processing(post_processing)]

    def get_map_functions(self):
        return [log_mapper]

    def get_reduce_functions(self):
        return [log_reducer]


def log_mapper(blocks, levels):
    res = zeros((1, len(levels)))
    for entry in sum(blocks, []):
        res += array([entry.count(level) for level in levels])

    return res


def post_processing(res):
    return res.tolist()


def log_reducer(blocks):
    return array(blocks).sum(axis=0)


if __name__ == '__main__':
    from os import getcwd

    from bdae.libpy.libbdaemanager import PyBDAEManager
    from bdae.libpy.libbdaescientist import PyBDAEScientist

    manager = PyBDAEManager("sofa:textdata:gateway:0")
    manager.create_dataset(LogEventParserData(name="Log Events", description="A MR	Job	Example"))
    manager.append_to_dataset("Log Events", getcwd() + "/testdata/logs.txt")

    def result_callback(res):
        print "The result is", ["%s: %s" % (level, int(count)) for level, count in zip(LEVELS, res)]

    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("Log Events", "count logs", [LEVELS], callback=result_callback)
