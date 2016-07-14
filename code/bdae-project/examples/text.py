# Created by Steffen Karlsson on 04-26-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from bdae.libpy.libbdaescientist import PyBDAEScientist

from examples.mobydick_word import MobyDickDatasetWord
from examples.mobydick_sentence import MobyDickDatasetSentence
from bdae.libpy.libbdaemanager import PyBDAEManager
from bdae.libweb import GatewayWebWrapper

LINK = "https://dl.dropboxusercontent.com/u/10746829/melville-moby_dick.txt"

if __name__ == '__main__':
    manager = PyBDAEManager("sofa:textdata:gateway:0")
    manager.create_dataset(MobyDickDatasetWord(name="moby dick word", description="Moby dick as words"))
    # manager.create_dataset(MobyDickDatasetSentence(name="moby dick sentence", description="Moby dick as sentence"))
    manager.append_to_dataset("moby dick word", LINK)

    def callback(res):
        print "Count:", res

    scientist = PyBDAEScientist("sofa:textdata:gateway:0")
    # GatewayWebWrapper(scientist).start(9990, hostname='0.0.0.0')
    scientist.submit_job("moby dick word", "count (neighborhood test)", "Moby Dick", callback=callback)
    # scientist.submit_job("moby dick word", "count", "Moby Dick", callback=callback)
