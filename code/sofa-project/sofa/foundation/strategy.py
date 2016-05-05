# Created by Steffen Karlsson on 05-06-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

class RoundRobin:
    """
    One-by-one fair share Round Robin distribution of data blocks.
    """
    def __init__(self):
        pass


class Tiles:
    """
    n-by-n, where n is num_tiles distribution of data blocks (including overlap on servers).
    """
    def __init__(self, num_tiles):
        self.num_tiles = num_tiles


class Linear:
    """
    Data blocks are split into n approximately equal sized blocks, where n is the number of servers,
    such that there is no overlap of data on any given server.
    """
    def __init__(self):
        pass
