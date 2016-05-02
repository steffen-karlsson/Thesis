# Created by Steffen Karlsson on 04-25-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from numpy import fromfile, float32, dot, divide, int32, rint, zeros, array, add, asarray

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist
from bdae.dataset import AbsMapReduceDataset
from sofa.operation import OperationContext
from os import getcwd

NUM_PROJECTIONS = 320
DETECTOR_ROWS = 192
DETECTOR_COLUMNS = 256


class FDKDataset(AbsMapReduceDataset):
    def get_reduce_functions(self):
        return [ndsum]

    def get_map_functions(self):
        return [fdkcore]

    def next_entry(self, data):
        for projection in data:
            yield projection

    def preprocess(self, data_ref):
        projections = fromfile(data_ref, dtype=float32)
        projections.shape = (NUM_PROJECTIONS, DETECTOR_ROWS, DETECTOR_COLUMNS)
        return projections

    def get_operations(self):
        return [
            OperationContext.by(self, "reconstruct", '[fdkcore, ndsum]').with_multiple_arguments(5)
        ]

    def postprocess(self, res):
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm

        path = getcwd() + "/test.png"

        plt.clf()
        plt.matshow(asarray(res), fignum=1, cmap=cm.Greys_r)
        plt.savefig(path)
        return path


def ndsum(data):
    return add.reduce(data).tolist()


def fdkcore(args):
    voxels = int(args[1])
    x_voxels = y_voxels = z_voxels = voxels

    combined_path = args[2]
    z_voxel_coords_path = args[3]
    transform_path = args[4]
    volumeweight_path = args[5]

    combined_matrix = fromfile(combined_path, dtype=float32)
    combined_matrix.shape = (4, x_voxels * y_voxels)

    z_voxel_coords = fromfile(z_voxel_coords_path, dtype=float32)

    transform_matrix = fromfile(transform_path, dtype=float32)
    transform_matrix.shape = (NUM_PROJECTIONS, 3, 4)

    volume_weight = fromfile(volumeweight_path, dtype=float32)
    volume_weight.shape = (NUM_PROJECTIONS, y_voxels * x_voxels)

    recon_volume = zeros((z_voxels, y_voxels, x_voxels), dtype=float32)

    projections = array(sum(list(args[0]), []))

    for p in xrange(NUM_PROJECTIONS):
        # Numpy FDK operates on flat arrays

        flat_proj_data = projections[p].ravel()

        for z in xrange(z_voxels):
            # Put current z voxel into combined_matrix

            combined_matrix[2, :] = z_voxel_coords[z]

            # Find the mapping between volume voxels and detector pixels
            # for the current angle

            vol_det_map = dot(transform_matrix[p], combined_matrix)
            map_cols = rint(divide(vol_det_map[0, :], vol_det_map[2, :])).astype(int32)
            map_rows = rint(divide(vol_det_map[1, :], vol_det_map[2, :])).astype(int32)

            # Find the detector pixels that contribute to the current slice
            # xrays that hit outside the detector area are masked out

            mask = (map_cols >= 0) & (map_rows >= 0) & (map_cols < DETECTOR_COLUMNS) & (map_rows < DETECTOR_ROWS)

            # The projection pixels that contribute to the current slice

            proj_indexs = map_cols * mask + map_rows * mask * DETECTOR_COLUMNS

            # Add the weighted projection pixel values to their
            # corresponding voxels in the z slice

            recon_volume[z].flat += flat_proj_data[proj_indexs] * volume_weight[p] * mask

    return recon_volume


if __name__ == '__main__':
    BASE_PATH = getcwd() + "/testdata/"

    manager = PyBDAEManager("sofa:textdata:gateway:0")
    manager.create_dataset(FDKDataset(name="FDK dataset", description="Testing reconstruction"))
    manager.append_to_dataset("FDK dataset", BASE_PATH + "projections.bin")

    def callback(res):
        print "Saved"

    args = ",".join(['64',
                     BASE_PATH + 'combined.bin',
                     BASE_PATH + 'z_voxel_coords.bin',
                     BASE_PATH + 'transform.bin',
                     BASE_PATH + 'volumeweight.bin'])
    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("FDK dataset", "reconstruct", args, callback=callback)