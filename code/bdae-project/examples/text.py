# Created by Steffen Karlsson on 04-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdae.libpy.libbdaescientist import PyBDAEScientist

from examples.mobydick_word import MobyDickDatasetWord
from bdae.libpy.libbdaemanager import PyBDAEManager

LINK = "https://dl.dropboxusercontent.com/u/10746829/melville-moby_dick.txt"

if __name__ == '__main__':
    manager = PyBDAEManager("sofa:textdata:gateway:0")
    manager.create_dataset(MobyDickDatasetWord(name="moby dick word", description="Moby dick as words"))
    manager.append_to_dataset("moby dick word", LINK)

    def callback(res):
        print "Count:", res

    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("moby dick word", "count", "Moby Dick", callback=callback)
