# Created by Steffen Karlsson on 07-29-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from os import getcwd

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist
from bdaeexamples.fdk import FDKDataset

if __name__ == '__main__':
    BASE_PATH = getcwd() + "/testdata/"

    manager = PyBDAEManager("sofa:textdata:gateway:0")
    dataset = FDKDataset(name="FDK dataset", description="Testing reconstruction")
    manager.create_dataset(dataset)
    manager.append_path_to_dataset(dataset, BASE_PATH + "projections.bin")


    def callback(res):
        print "Saved: ", res


    args = [64,
            BASE_PATH + 'combined.bin',
            BASE_PATH + 'z_voxel_coords.bin',
            BASE_PATH + 'transform.bin',
            BASE_PATH + 'volumeweight.bin']
    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("FDK dataset", "reconstruct", args, callback=callback)
