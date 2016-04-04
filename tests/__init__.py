import unittest
import test_miracl_api


def test_suite():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_miracl_api)
    return suite
