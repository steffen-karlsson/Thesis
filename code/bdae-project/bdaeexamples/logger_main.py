# Created by Steffen Karlsson on 06-13-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdaeexamples.logger import LogEventParserData

LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

if __name__ == '__main__':
    from os import getcwd

    from bdae.libpy.libbdaemanager import PyBDAEManager
    from bdae.libpy.libbdaescientist import PyBDAEScientist

    manager = PyBDAEManager("sofa:textdata:gateway:0")
    dataset = LogEventParserData(name="Log Events", description="A MR	Job	Example")
    manager.create_dataset(dataset)
    manager.append_path_to_dataset(dataset, getcwd() + "/testdata/logs.txt")


    def result_callback(res):
        print "The result is", ["%s: %s" % (level, int(count)) for level, count in zip(LEVELS, res)]


    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("Log Events", "count logs", [LEVELS], callback=result_callback)
