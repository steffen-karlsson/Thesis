# Created by Steffen Karlsson on 02-23-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from math import log


class TreeBarrier:
    def __init__(self, current, nodes, root):
        self.__nodes = nodes
        self.__id = (self.__nodes.index(current) - self.__nodes.index(root)) % len(self.__nodes)
        self.__offset = 0 - self.__nodes.index(root)
        self.__sending_itr = 0
        self.__max_itr = int(log(len(self.__nodes), 2))
        self.__step = lambda itr: pow(2, itr + 1)
        self.__start = lambda itr: pow(2, itr)
        self.has_send = False

    def should_send(self, itr):
        if self.has_send:
            return False

        if itr == self.__max_itr:
            raise StopIteration

        tmp = float(self.__id / self.__start(itr))
        if not tmp.is_integer():
            return False

        if tmp % 2 == 1:
            self.has_send = True
            self.__sending_itr = int(itr)
            return True

        return False

    def get_receiver_idx(self):
        # Note normally root isn't part of others list, thats why the -1
        return self.__id - self.__start(self.__sending_itr) - self.__offset - 1
