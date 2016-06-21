# Created by Steffen Karlsson on 03-31-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta
import string
import __builtin__

from nltk import word_tokenize, sent_tokenize

from bdae.templates.import_utils import map_function_binder, module_binder, reduce_function_binder
from bdae.dataset import AbsMapReduceDataset


class _TextData(AbsMapReduceDataset):
    __metaclass__ = ABCMeta

    def get_map_functions(self):
        return module_binder(string, map_function_binder, ['count'], new_fun_names=['count_occurrences'])

    def get_reduce_functions(self):
        return module_binder(__builtin__, reduce_function_binder, ['sum', 'min', 'max'])


class TextDataByWord(_TextData):
    __metaclass__ = ABCMeta

    def next_entry(self, data):
        for word in word_tokenize(data):
            yield word


class TextDataBySentence(_TextData):
    __metaclass__ = ABCMeta

    def next_entry(self, data):
        for sentence in sent_tokenize(data):
            yield sentence

class TextDataByLine(_TextData):
    __metaclass__ = ABCMeta

    def next_entry(self, data):
        return data.splitlines()
