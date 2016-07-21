# Created by Steffen Karlsson on 02-19-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdae.templates.text_dataset import TextDataByLine
from sofa.foundation.base import load_data_by_url
from sofa.foundation.operation import OperationContext


class MobyDickDatasetLine(TextDataByLine):
    def preprocess(self, data_ref):
        return load_data_by_url(data_ref)

    def get_operations(self):
        return [
            OperationContext.by(self, "count", '[count_occurrences, sum]'),
        ]
