# Created by Steffen Karlsson on 02-18-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from cPickle import dumps as cdumps, loads as cloads
from hmac import new
from hashlib import sha256
from bdos.utils import find_identifier, STATUS_INVALID_DATA


def __generate_digest(data):
    return new(find_identifier(__generate_digest.__module__), data, sha256).hexdigest()


def secure_send(data, fun):
    fun(secure(data))


def secure_load(bundle):
    digist, pdata = bundle

    if isinstance(pdata, unicode):
        pdata = pdata.encode("ascii")

    if digist != __generate_digest(pdata):
        return STATUS_INVALID_DATA

    return cloads(pdata)

def secure(data):
    pdata = cdumps(data)
    return __generate_digest(pdata), pdata