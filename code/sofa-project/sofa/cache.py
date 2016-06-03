# Created by Steffen Karlsson on 02-25-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

class CacheSystem:
    def __init__(self, cache_type, args=None):
        if args:
            self.__data = cache_type(args)
        else:
            self.__data = cache_type()

    def put(self, key, value):
        self.__data[key] = value

    def get(self, key):
        return self.__data[key]

    def delete(self, key):
        if self.contains(key):
            del self.__data[key]

    def contains(self, key):
        return key in self.__data

    def keys(self):
        return self.__data.keys()