# Created by Steffen Karlsson on 02-19-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sofa.foundation.base import load_data_by_path, load_data_by_url
from bdae.templates.text_dataset import TextDataByWord
from sofa.foundation.operation import OperationContext, Sequential, Parallel
from sofa.foundation.strategy import Tiles


class MobyDickDatasetWord(TextDataByWord):
    def preprocess(self, data_ref):
        return load_data_by_path(data_ref)

    def get_map_functions(self):
        return super(MobyDickDatasetWord, self).get_map_functions() + [nothing]

    def get_operations(self):
        return [
            OperationContext.by(self, "count (neighborhood test)",
                                '[nothing, neighborhood:1:1, modify:block_formatter, count_occurrences, sum]'),
            OperationContext.by(self, "count", '[modify:block_formatter, count_occurrences, sum]')
        ]

    def get_distribution_strategy(self):
        return Tiles(2)

    def get_replication_factor(self):
        return 1


def block_formatter(block_gen):
    return [" ".join(block) for block in block_gen]


def nothing(blocks, args):
    return blocks
