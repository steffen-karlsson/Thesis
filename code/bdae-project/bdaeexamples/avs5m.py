# Created by Steffen Karlsson on 04-30-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from os import getcwd

from numpy import arange, pad, array, mean, power, less, log, bool, concatenate, \
    ones, floor, sum as npsum, logical_and, size, int, empty, equal, min_scalar_type, max as npmax
from numpy.core.multiarray import bincount
from numpy.lib import stride_tricks, median
from tifffile import imread

from bdae.libpy.libbdaescientist import PyBDAEScientist
from sofa.foundation.operation import OperationContext
from sofa.foundation.strategy import Tiles
from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.templates.image_dataset import ImageDataset


# Strength of median filter
L = 5

PIXEL_DIST = 16

# Size pixel for eroding
ERODE_SIZE = 3

# Coordinates for the finger on right hand side
X, Y = 566, 362

# Distance from coordinates
M = arange(-30, 31)

# Number of slices to process
NUM_SLICES = 2

# Erode dimension
D = ERODE_SIZE * 2 + 1

# Groups
NUM_GROUPS = 4

MAX_ITER = 1000000

STREL = ones((D, D, D), dtype=bool)
STREL[0, 0, 0] = False
STREL[0, 0, -1] = False
STREL[0, -1, 0] = False
STREL[-1, 0, 0] = False
STREL[0, -1, -1] = False
STREL[-1, 0, -1] = False
STREL[-1, -1, 0] = False
STREL[-1, -1, -1] = False


class AVS5MDataset(ImageDataset):
    def image_loader(self, path_or_url):
        return imread(path_or_url)

    def get_operations(self):
        return [
            OperationContext.by(self, "circle recognition", '[median_filter, thresholding, '
                                                            'eroding, connected_components, find_groups]')
        ]

    def next_entry(self, data):
        for i in xrange(NUM_SLICES):
            yield data[i, ...]

    def get_reduce_functions(self):
        return [find_groups]

    def get_map_functions(self):
        return [median_filter, thresholding, eroding, connected_components]

    def get_distribution_strategy(self):
        return Tiles(2)


def median_filter(blocks):
    # Flatten blocks to one large, assuming linear distributions model such that all blocks are alligned
    image = concatenate(blocks)
    median_image = empty(image.shape)
    window_size = array((L, L))

    for i in xrange(len(image)):
        im = pad(image[i, ...], L / 2, 'edge')
        shape = array(im.shape)

        # Amount of slices in each dimension
        slice_shape = tuple((shape - window_size) + 1) + tuple(window_size)

        # Strides will cut away the padding
        slices = stride_tricks.as_strided(im, shape=slice_shape, strides=(im.strides + im.strides))
        median_image[i, ...] = median(slices, axis=(-1, -2))

    return [median_image]


def thresholding(blocks):
    # Flatten blocks to one large, assuming linear distributions model such that all blocks are alligned
    median_image = concatenate(blocks)
    v = mean(median_image[0][Y + M].T[X + M])
    return [less(log(power(median_image - v, 2) + 1), PIXEL_DIST)]


def eroding(blocks):
    # Flatten blocks to one large, assuming linear distributions model such that all blocks are alligned
    thresholded_image = concatenate(blocks)

    w = int(floor(len(STREL) / 2))
    im = pad(thresholded_image, w, 'constant', constant_values=True)

    window_size = array(STREL.shape)
    shape = array(im.shape)

    # Slices in each dimension
    slice_shape = tuple((shape - window_size) + 1) + tuple(window_size)

    # Strides will cut away the padding
    slices = stride_tricks.as_strided(
        im,
        shape=slice_shape,
        strides=(im.strides + im.strides))

    partial_erode = logical_and(slices[:, :, :], STREL)
    partial_erode = equal(partial_erode, STREL)

    return [npsum(partial_erode, axis=(-1, -2, -3)) == size(STREL)]


def connected_components(blocks):
    # Flatten blocks to one large, assuming linear distributions model such that all blocks are alligned
    eroded_image = concatenate(blocks)

    # Find minimum data type to hold result (fit max-label)
    min_dtype = min_scalar_type(size(eroded_image))

    # Pad image with False (background)
    im = pad(eroded_image, 1, 'constant', constant_values=False)

    # Init result labels as 1..n. Remove background entries
    result = (arange(1, size(im) + 1, dtype=min_dtype)).reshape(im.shape) * im

    # Keep track of sum
    old_sum, new_sum = 0, 0

    for i in xrange(MAX_ITER):
        # Jacobi stencil update of right,left,up,down,in,out neighbours
        result[1:-1, 1:-1, 1:-1] = npmax(array([
            result[1:-1, 1:-1, 1:-1],
            result[1:-1, 1:-1, :-2],
            result[1:-1, :-2, 1:-1],
            result[:-2, 1:-1, 1:-1],
            result[1:-1, 1:-1, 2:],
            result[1:-1, 2:, 1:-1],
            result[2:, 1:-1, 1:-1]
        ]), axis=0)

        # Remove background
        result *= im

        # We are done, if the sum hasn't changed
        new_sum = npsum(result)
        if old_sum == new_sum:
            print "Broke after iteration:", i
            break
        else:
            old_sum = new_sum

    # Remove padding from image
    return [result[1:-1, 1:-1, 1:-1]]


def find_groups(blocks):
    # Flatten blocks to one large, assuming linear distributions model such that all blocks are alligned
    connected_components = concatenate(blocks)
    return bincount(connected_components.ravel()).argsort()[-NUM_GROUPS - 1:-1][::-1].tolist()


if __name__ == '__main__':
    BASE_PATH = getcwd() + "/testdata/"
    manager = PyBDAEManager("sofa:textdata:gateway:0")
    manager.create_dataset(AVS5MDataset(name="AVS5M dataset", description="Testing image circle recognition"))
    manager.append_to_dataset("AVS5M dataset", BASE_PATH + "AVS5M.tif")
    print "Appended"

    def callback(res):
        print "The result is: " + str(res)

    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("AVS5M dataset", "circle recognition", None, callback=callback)
