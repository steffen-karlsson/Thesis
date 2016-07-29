# Created by Steffen Karlsson on 04-30-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from os import getcwd

from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libpy.libbdaescientist import PyBDAEScientist
from bdaeexamples.avs5m import AVS5MDataset

if __name__ == '__main__':
    BASE_PATH = getcwd() + "/testdata/"
    manager = PyBDAEManager("sofa:textdata:gateway:0")
    dataset = AVS5MDataset(name="AVS5M dataset", description="Testing image circle recognition")
    manager.create_dataset(dataset)
    manager.append_path_to_dataset(dataset, BASE_PATH + "AVS5M.tif")
    print "Appended"


    def callback(res):
        print "The result is: " + str(res)


    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("AVS5M dataset", "circle recognition", None, callback=callback)
