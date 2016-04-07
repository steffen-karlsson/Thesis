# Created by Steffen Karlsson on 02-11-2016
# Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.

STATUS_SUCCESS = 200
STATUS_PROCESSING = 202
STATUS_INVALID_DATA = 400
STATUS_NOT_FOUND = 404
STATUS_NOT_ALLOWED = 405
STATUS_ALREADY_EXISTS = 409
STATUS_NO_DATA = 410

CODES = [STATUS_INVALID_DATA, STATUS_NOT_FOUND, STATUS_NOT_ALLOWED, STATUS_ALREADY_EXISTS, STATUS_NO_DATA]


def verify_error(args):
    if isinstance(args, tuple):
        res, message = args
    else:
        res = args
        message = ""

    if is_error(res):
        raise __get_exception_from_status(res, message)


def is_processing(res):
    if isinstance(res, tuple):
        # First argument is always status code
        res = res[0]
    return res == STATUS_PROCESSING


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

    if res == STATUS_NO_DATA:
        return NoDataInDatasetException(message)

    return Exception(message)


class DatasetAlreadyExistsException(Exception):
    def __init__(self, message):
        super(DatasetAlreadyExistsException, self).__init__(message)


class DatasetNotExistsException(Exception):
    def __init__(self, message):
        super(DatasetNotExistsException, self).__init__(message)


class NoDataInDatasetException(Exception):
    def __init__(self, message):
        super(NoDataInDatasetException, self).__init__(message)
