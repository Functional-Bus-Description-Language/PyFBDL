import unittest

from fbdl.packages import Packages

packages = Packages()

packages['foo'] = [
    {'Path': "/zero/fbd-foo"},
    {'Path': "/zero/one/fbd-foo"},
    {'Path': "/zero/one/two/fbd-foo"},
]


packages['bar'] = [{'Path': "/some/path/fbd/bar"}]


class TestGettingRefToPackage(unittest.TestCase):
    def test_get_ref_to_foo(self):
        ref = packages.get_ref_to_pkg("zero/fbd-foo")
        self.assertEqual(ref, packages['foo'][0])

        ref = packages.get_ref_to_pkg("zero/one/fbd-foo")
        self.assertEqual(ref, packages['foo'][1])

        ref = packages.get_ref_to_pkg("two/fbd-foo")
        self.assertEqual(ref, packages['foo'][2])

    def test_get_ref_to_bar(self):
        ref = packages.get_ref_to_pkg("bar")
        self.assertEqual(ref, packages['bar'][0])
