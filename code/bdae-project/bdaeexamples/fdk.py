# Created by Steffen Karlsson on 04-25-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from cPickle import dumps, loads
from os import getcwd

from numpy import fromfile, float32, dot, divide, int32, rint, zeros, add, asarray, concatenate, ceil

from bdae.dataset import AbsMapReduceDataset
from sofa.foundation.operation import OperationContext, ExpectedReturnType

NUM_PROJECTIONS = 320
DETECTOR_ROWS = 192
DETECTOR_COLUMNS = 256


class FDKDataset(AbsMapReduceDataset):
    def get_reduce_functions(self):
        return [ndsum]

    def get_map_functions(self):
        return [fdkcore]

    def serialize(self, data):
        return dumps(data)

    def deserialize(self, data):
        if isinstance(data, unicode):
            data = data.encode("ascii")

        return loads(data)

    def is_serialized(self):
        return True

    def next_entry(self, data):
        for projection in data:
            yield projection

    def preprocess(self, data_ref):
        projections = fromfile(data_ref, dtype=float32)
        projections.shape = (NUM_PROJECTIONS, DETECTOR_ROWS, DETECTOR_COLUMNS)
        return projections

    def get_operations(self):
        return [
            OperationContext.by(self, "reconstruct", '[fdkcore, ndsum]')
                .with_post_processing(post_process)
                .with_expected_return_type(ExpectedReturnType.Image)
                .with_meta_data()
        ]


def post_process(res):
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    path = getcwd() + "/test.png"
    plt.clf()
    plt.matshow(add.reduce(asarray(res)), fignum=1, cmap=cm.Greys_r)
    plt.savefig(path)
    return path


def ndsum(blocks, meta_data):
    return add.reduce(blocks)


def fdkcore(blocks, meta_data, voxels, combined_path, z_voxel_coords_path, transform_path, volumeweight_path):
    # Flatten blocks to one large, assuming linear distributions model such that all blocks are alligned
    x_voxels = y_voxels = z_voxels = voxels

    combined_matrix = fromfile(combined_path, dtype=float32)
    combined_matrix.shape = (4, x_voxels * y_voxels)

    z_voxel_coords = fromfile(z_voxel_coords_path, dtype=float32)

    transform_matrix = fromfile(transform_path, dtype=float32)
    transform_matrix.shape = (NUM_PROJECTIONS, 3, 4)

    projections = concatenate(blocks)

    recon_volume = zeros((len(projections), z_voxels, y_voxels, x_voxels), dtype=float32)

    offset = ceil(NUM_PROJECTIONS / meta_data['num-storage-nodes']) * meta_data['idx']

    for z in xrange(z_voxels):
        combined_matrix[2, :] = z_voxel_coords[z]

        for p, proj in enumerate(projections):
            vol_det_map = dot(transform_matrix[p + offset], combined_matrix)
            rint_map = rint(divide(vol_det_map[0:2, :], vol_det_map[2, :]))
            map_col = rint_map[0]
            map_row = rint_map[1]

            mask = (map_col >= 0) & (map_row >= 0) & \
                   (map_col < DETECTOR_COLUMNS) & (map_row < DETECTOR_ROWS)

            recon_volume[p][z].flat += proj.flatten()[
                (mask * (map_col + map_row * DETECTOR_COLUMNS)).astype(int32)
            ]

    return recon_volume
