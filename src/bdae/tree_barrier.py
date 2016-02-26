# Created by Steffen Karlsson on 02-23-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from math import log


class TreeBarrier:
    def __init__(self, current, nodes, root):
        self.__nodes = nodes
        self.__offset = 0 - nodes.index(root)
        self.__id = nodes.index(current) + self.__offset
        self.__sending_itr = 0
        self.__max_itr = int(log(len(nodes), 2))
        self.__step = lambda itr: pow(2, itr + 1)
        self.__start = lambda itr: pow(2, itr)
        self.has_send = False

    def should_send(self, itr):
        if itr == self.__max_itr:
            raise StopIteration

        if self.has_send:
            return False

        tmp = float(self.__id / self.__start(itr))
        if not tmp.is_integer():
            return False

        if tmp % 2 == 1:
            self.has_send = True
            self.__sending_itr = int(itr)
            return True

        return False

    def get_receiver(self):
        return self.__nodes[self.__id - self.__start(self.__sending_itr) - self.__offset]


if __name__ == '__main__':
    tb = TreeBarrier("foo-0", ["foo-" + str(i) for i in range(0, 16)], "foo-8")
    try:
        while True:
            if tb.should_send():
                print "Sending"
                print tb.get_receiver()
            else:
                print "Shouldn't send"
    except StopIteration:
        pass
