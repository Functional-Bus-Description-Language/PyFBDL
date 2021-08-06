import unittest
import os

from fbdl import pre


class TestPackageDiscovery(unittest.TestCase):
    def test_package_discovery(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        dummy_project_dir = os.path.join(test_dir, "dummy_project")
        os.chdir(dummy_project_dir)

        dummy_env_dir = os.path.join(test_dir, "dummy_env/fbd")
        os.environ["FBDPATH"] = dummy_env_dir

        packages = pre.discover_packages()

        expected = {
            "bar": [os.path.join(dummy_project_dir, "fbd/fbd-bar")],
            "foo": [os.path.join(dummy_project_dir, "fbd/foo")],
            "baz": [
                os.path.join(dummy_env_dir, "baz"),
                os.path.join(dummy_project_dir, "submodules/some_lib/fbd-baz"),
            ],
        }

        self.assertEqual(packages, expected)
