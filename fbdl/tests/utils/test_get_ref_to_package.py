import unittest

from fbdl import utils


packages = {
    'foo': [
        {'Path': "/zero/fbd-foo"},
        {'Path': "/zero/one/fbd-foo"},
        {'Path': "/zero/one/two/fbd-foo"},
    ],
    'bar': [
        {
            'Path': "/some/path/fbd/bar",
        }
    ],
}


class TestGettingRefToPackage(unittest.TestCase):
    def test_get_ref_to_foo(self):
        ref = utils.get_ref_to_package("zero/fbd-foo", packages)
        self.assertEqual(ref, packages['foo'][0])

        ref = utils.get_ref_to_package("zero/one/fbd-foo", packages)
        self.assertEqual(ref, packages['foo'][1])

        ref = utils.get_ref_to_package("two/fbd-foo", packages)
        self.assertEqual(ref, packages['foo'][2])

    def test_get_ref_to_bar(self):
        ref = utils.get_ref_to_package("bar", packages)
        self.assertEqual(ref, packages['bar'][0])
