import unittest
import os

from fbdl import pre

from pprint import pprint


class TestPackageDiscovery(unittest.TestCase):
    def test_package_discovery(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        dummy_project_dir = os.path.join(test_dir, "dummy_project")
        os.chdir(dummy_project_dir)

        dummy_env_dir = os.path.join(test_dir, "dummy_env/fbd")
        os.environ["FBDPATH"] = dummy_env_dir

        packages = pre.discover_packages()

        expected = {
            'bar': [
                {
                    'Files': [
                        {'Path' : "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/fbd/fbd-bar/b.fbd"}
                    ],
                    'Path': "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/fbd/fbd-bar",
                }
            ],
            'baz': [
                {
                    'Files': [
                        {'Path' : "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_env/fbd/baz/d.fbd"}
                    ],
                    'Path': "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_env/fbd/baz",
                },
                {
                    'Files': [
                        {'Path' : "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/submodules/some_lib/fbd-baz/c.fbd"}
                    ],
                    'Path': "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/submodules/some_lib/fbd-baz",
                },
            ],
            'foo': [
                {
                    'Files': [
                        {'Path' : "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/fbd/foo/z.fbd"},
                        {'Path' : "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/fbd/foo/a.fbd"},
                    ],
                    'Path': "/home/mkru/workspace/FBDL/PyFBDL/fbdl/tests/pre/dummy_project/fbd/foo",
                }
            ],
        }

        for package, list_ in expected.items():
            self.assertEqual(package in packages, True)
            for i, pkg in enumerate(list_):
                self.assertEqual(pkg['Path'], packages[package][i]['Path'])
                for j, f in enumerate(pkg['Files']):
                    self.assertEqual(f['Path'], packages[package][i]['Files'][j]['Path'])

        for package, list_ in packages.items():
            for pkg in list_:
                for f in pkg['Files']:
                    f['Handle'].close()
