# Created by Steffen Karlsson on 04-08-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdae.templates.number_dataset import NumpyArrayDataset
from sofa.foundation.operation import OperationContext


class NetCDFNumpyDataset(NumpyArrayDataset):
    def get_operations(self):
        return [
            OperationContext.by(self, 'unit sum', '[sink, sum]').with_multiple_arguments(),
            OperationContext.by(self, 'unit maximum', '[sink, max]').with_multiple_arguments(),
            OperationContext.by(self, 'unit minumum', '[sink, min]').with_multiple_arguments(),
            OperationContext.by(self, 'unit reduction', '[sink, add.reduce]').with_multiple_arguments(),
            OperationContext.by(self, 'unit average', '[sink, sum]')
                .with_multiple_arguments().with_post_processing(unit_average_post_process),

            OperationContext.by(self, 'set sum', '[sum, sink]').with_multiple_arguments(),
            OperationContext.by(self, 'set maximum', '[max, sink]').with_multiple_arguments(),
            OperationContext.by(self, 'set minumum', '[min, sink]').with_multiple_arguments(),
            OperationContext.by(self, 'set reduction', '[add.reduce sink]').with_multiple_arguments(),
            OperationContext.by(self, 'set average', '[average, sink]').with_multiple_arguments(),
        ]

    def next_entry(self, data):
        yield data

    def preprocess(self, data_ref):
        return data_ref


def unit_average_post_process(blocks, args):
    pass


def sink(blocks, args):
    return blocks, args
