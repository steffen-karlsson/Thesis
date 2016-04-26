# Created by Steffen Karlsson on 02-19-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from sofa.base import load_data_by_url
from bdae.templates.text_dataset import TextDataByWord
from sofa.operation import OperationContext


class MobyDickDatasetWord(TextDataByWord):
    def preprocess(self, data_ref):
        return load_data_by_url(data_ref)

    def get_operations(self):
        return [
            OperationContext.by(self, "count", '[count_occurrences, sum]'),
        ]

    def get_block_stride(self):
        return 2
