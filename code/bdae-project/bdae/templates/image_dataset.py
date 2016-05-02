# Created by Steffen Karlsson on 04-30-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from abc import ABCMeta, abstractmethod

from numpy import array, float32

from bdae.dataset import AbsMapReduceDataset


class ImageDataset(AbsMapReduceDataset):
    __metaclass__ = ABCMeta

    def preprocess(self, path_or_url):
        return array(self.image_loader(path_or_url), dtype=float32)

    @abstractmethod
    def image_loader(self, path_or_url):
        pass
