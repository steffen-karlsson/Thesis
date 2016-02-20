# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

from hashlib import sha256


def find_identifier(name):
    return sha256(name).hexdigest().encode('ascii')


def import_class(cls):
    package, classname = cls.rsplit('.', 1)
    m = __import__(package, globals(), locals(), [classname])
    return getattr(m, classname)

# Error codes
STATUS_SUCCESS = 200
STATUS_INVALID_DATA = 400
STATUS_NOT_FOUND = 404
STATUS_NOT_ALLOWED = 405
STATUS_ALREADY_EXISTS = 409

CODES = [STATUS_INVALID_DATA, STATUS_NOT_FOUND, STATUS_NOT_ALLOWED, STATUS_ALREADY_EXISTS]


def verify_error(res, message=""):
    if is_error(res):
        raise __get_exception_from_status(res, message)


def is_error(res):
    return res in CODES


def __get_exception_from_status(res, message):
    if res == STATUS_NOT_FOUND:
        return DatasetNotExistsException(message)

    if res == STATUS_ALREADY_EXISTS:
        return DatasetAlreadyExistsException(message)

    return Exception(message)


class DatasetAlreadyExistsException(Exception):
    def __init__(self, message):
        super(DatasetAlreadyExistsException, self).__init__(message)


class DatasetNotExistsException(Exception):
    def __init__(self, message):
        super(DatasetNotExistsException, self).__init__(message)
