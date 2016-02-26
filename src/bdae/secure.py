# Created by Steffen Karlsson on 02-18-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from cPickle import dumps as cdumps, loads as cloads
from hmac import new
from hashlib import sha256
from bdae.utils import STATUS_INVALID_DATA


def __generate_digest(data):
    return new(sha256(__generate_digest.__module__).hexdigest(), data, sha256).hexdigest()


def secure_send(data, fun):
    fun(secure(data))


def secure_load(bundle):
    digest, pdata = bundle
    return secure_load2(digest, pdata)


def secure_load2(digest, pdata):
    if isinstance(pdata, unicode):
        pdata = pdata.encode("ascii")

    return validate(pdata, digest)


def secure(data):
    pdata = cdumps(data)
    return __generate_digest(pdata), pdata


def validate(pdata, digest):
    if digest != __generate_digest(pdata):
        return STATUS_INVALID_DATA

    return cloads(pdata)
