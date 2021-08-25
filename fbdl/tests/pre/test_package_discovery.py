import unittest
import os
path_prefix = '/'.join(os.path.abspath(__file__).split('/')[:-4]) + '/'

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
                        {'Path' : path_prefix + "fbdl/tests/pre/dummy_project/fbd/fbd-bar/b.fbd"}
                    ],
                    'Path': path_prefix + "fbdl/tests/pre/dummy_project/fbd/fbd-bar",
                }
            ],
            'baz': [
                {
                    'Files': [
                        {'Path' : path_prefix + "fbdl/tests/pre/dummy_env/fbd/baz/d.fbd"}
                    ],
                    'Path': path_prefix + "fbdl/tests/pre/dummy_env/fbd/baz",
                },
                {
                    'Files': [
                        {'Path' : path_prefix + "fbdl/tests/pre/dummy_project/submodules/some_lib/fbd-baz/c.fbd"}
                    ],
                    'Path': path_prefix + "fbdl/tests/pre/dummy_project/submodules/some_lib/fbd-baz",
                },
            ],
            'foo': [
                {
                    'Files': [
                        {'Path' : path_prefix + "fbdl/tests/pre/dummy_project/fbd/foo/a.fbd"},
                        {'Path' : path_prefix + "fbdl/tests/pre/dummy_project/fbd/foo/z.fbd"},
                    ],
                    'Path': path_prefix + "fbdl/tests/pre/dummy_project/fbd/foo",
                }
            ],
        }

        for pkg_name, pkgs in expected.items():
            self.assertEqual(pkg_name in packages, True)
            for i, pkg in enumerate(pkgs):
                self.assertEqual(pkg['Path'], packages[pkg_name][i]['Path'])
                for j, f in enumerate(pkg['Files']):
                    self.assertEqual(f['Path'], packages[pkg_name][i]['Files'][j]['Path'])

        for pkg_name, pkgs in packages.items():
            for pkg in pkgs:
                for f in pkg['Files']:
                    f['Handle'].close()
