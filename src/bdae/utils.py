# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

def find_identifier(name, mod):
    identifier = hash(name)
    return identifier if mod is None else identifier % mod

# Error codes
STATUS_SUCCESS = 200
STATUS_PROCESSING = 202
STATUS_INVALID_DATA = 400
STATUS_NOT_FOUND = 404
STATUS_NOT_ALLOWED = 405
STATUS_ALREADY_EXISTS = 409

CODES = [STATUS_PROCESSING, STATUS_INVALID_DATA, STATUS_NOT_FOUND, STATUS_NOT_ALLOWED, STATUS_ALREADY_EXISTS]


def verify_error(args):
    if isinstance(args, tuple):
        res, message = args
    else:
        res = args
        message = ""

    if is_error(res):
        raise __get_exception_from_status(res, message)


def is_error(res):
    if isinstance(res, tuple):
        # First argument is always status code
        res = res[0]
    return res in CODES


def __get_exception_from_status(res, message):
    if res == STATUS_NOT_FOUND:
        return DatasetNotExistsException(message)

    if res == STATUS_ALREADY_EXISTS:
        return DatasetAlreadyExistsException(message)

    if res == STATUS_NOT_ALLOWED:
        return NotImplementedError(message)

    return Exception(message)


class DatasetAlreadyExistsException(Exception):
    def __init__(self, message):
        super(DatasetAlreadyExistsException, self).__init__(message)


class DatasetNotExistsException(Exception):
    def __init__(self, message):
        super(DatasetNotExistsException, self).__init__(message)
