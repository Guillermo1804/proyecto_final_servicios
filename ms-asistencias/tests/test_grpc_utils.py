import os
import sys
import unittest

from grpc import StatusCode

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from grpc_utils import map_grpc_error


class FakeRpcError:
    def __init__(self, code, details):
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details


class TestMapGrpcError(unittest.TestCase):
    def test_not_found(self):
        e = FakeRpcError(StatusCode.NOT_FOUND, 'no existe')
        with self.assertRaises(LookupError):
            map_grpc_error(e)

    def test_deadline(self):
        e = FakeRpcError(StatusCode.DEADLINE_EXCEEDED, 'timeout')
        with self.assertRaises(TimeoutError):
            map_grpc_error(e)


if __name__ == '__main__':
    unittest.main()
