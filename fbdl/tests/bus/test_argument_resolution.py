import unittest

from fbdl import bus


class TestArgumentResolution(unittest.TestCase):
    def test_only_positional_no_default_values(self):
        param_list = ({'Name': 'a'}, {'Name': 'b'})
        symbol = {'Argument List': ({'Value': 1}, {'Value': 2})}
        expected = {'a': 1, 'b': 2}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_only_positional_overwrite_default_values(self):
        param_list = (
            {'Name': 'a', 'Default Value': 101},
            {'Name': 'b', 'Default Value': 102},
        )
        symbol = {'Argument List': ({'Value': 1}, {'Value': 2})}
        expected = {'a': 1, 'b': 2}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_positional_with_one_default_value(self):
        param_list = ({'Name': 'a'}, {'Name': 'b'}, {'Name': 'c', 'Default Value': 3})
        symbol = {'Argument List': ({'Value': 1}, {'Value': 2})}
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_positional_with_one_named(self):
        param_list = ({'Name': 'a'}, {'Name': 'b'}, {'Name': 'c'})
        symbol = {
            'Argument List': ({'Value': 1}, {'Value': 2}, {'Name': 'c', 'Value': 3})
        }
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_no_argument_list_at_all(self):
        param_list = (
            {'Name': 'a', 'Default Value': 1},
            {'Name': 'b', 'Default Value': 2},
            {'Name': 'c', 'Default Value': 3},
        )
        symbol = {}
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_all_named_arguments_no_default_values(self):
        param_list = ({'Name': 'a'}, {'Name': 'b'}, {'Name': 'c'})
        symbol = {
            'Argument List': (
                {'Name': 'b', 'Value': 2},
                {'Name': 'c', 'Value': 3},
                {'Name': 'a', 'Value': 1},
            )
        }
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_all_named_arguments_and_default_values(self):
        param_list = ({'Name': 'a', 'Default Value': 1}, {'Name': 'b'}, {'Name': 'c'})
        symbol = {
            'Argument List': ({'Name': 'b', 'Value': 2}, {'Name': 'c', 'Value': 3})
        }
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))

    def test_only_named_overwrite_default_values(self):
        param_list = (
            {'Name': 'a', 'Default Value': 101},
            {'Name': 'b', 'Default Value': 102},
        )
        symbol = {
            'Argument List': ({'Name': 'a', 'Value': 1}, {'Name': 'b', 'Value': 2})
        }
        expected = {'a': 1, 'b': 2}
        self.assertEqual(expected, bus.resolve_argument_list(symbol, param_list))
