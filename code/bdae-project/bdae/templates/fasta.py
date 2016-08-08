# Created by Steffen Karlsson on 08-05-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta

from Bio import SeqIO
from Bio.Blast.NCBIWWW import qblast

from bdae.dataset import AbsMapReduceDataset
from sofa.foundation.base import load_data_by_path


class FastaDataset(AbsMapReduceDataset):
    __metaclass__ = ABCMeta

    def get_reduce_functions(self):
        return [sink]

    def get_map_functions(self):
        return [blast]

    def next_entry(self, data):
        for seqio in data:
            yield seqio.seq

    def preprocess(self, data_ref):
        return SeqIO.parse(load_data_by_path(data_ref), "fasta")


def sink(blocks):
    return sum(blocks, [])


def blast(blocks, database):
    return [qblast('blastn', database, block) for block in blocks]
