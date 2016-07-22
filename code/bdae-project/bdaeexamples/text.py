# Created by Steffen Karlsson on 04-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdae.libpy.libbdaescientist import PyBDAEScientist

from bdaeexamples.mobydick_word import MobyDickDatasetWord
from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libweb import GatewayWebWrapper

LINK = "Insert link to Moby Dick"

if __name__ == '__main__':
    manager = PyBDAEManager("sofa:textdata:gateway:0")
    dataset = MobyDickDatasetWord(name="moby dick word", description="Moby dick as words")
    manager.create_dataset(dataset)
    manager.append_path_to_dataset(dataset, LINK)


    def callback(res):
        print "Count:", res


    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    scientist.submit_job("moby dick word", "count", "Moby Dick", callback=callable)
    # GatewayWebWrapper(scientist).start(9990, hostname='0.0.0.0')
