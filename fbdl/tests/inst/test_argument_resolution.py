import unittest

from fbdl.inst import args


class TestArgumentResolution(unittest.TestCase):
    def test_only_positional_no_default_values(self):
        params = ({'Name': 'a'}, {'Name': 'b'})
        symbol = {'Arguments': ({'Value': 1}, {'Value': 2})}
        expected = {'a': 1, 'b': 2}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_only_positional_overwrite_default_values(self):
        params = (
            {'Name': 'a', 'Default Value': 101},
            {'Name': 'b', 'Default Value': 102},
        )
        symbol = {'Arguments': ({'Value': 1}, {'Value': 2})}
        expected = {'a': 1, 'b': 2}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_positional_with_one_default_value(self):
        params = ({'Name': 'a'}, {'Name': 'b'}, {'Name': 'c', 'Default Value': 3})
        symbol = {'Arguments': ({'Value': 1}, {'Value': 2})}
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_positional_with_one_named(self):
        params = ({'Name': 'a'}, {'Name': 'b'}, {'Name': 'c'})
        symbol = {
            'Arguments': ({'Value': 1}, {'Value': 2}, {'Name': 'c', 'Value': 3})
        }
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_no_argument_list_at_all(self):
        params = (
            {'Name': 'a', 'Default Value': 1},
            {'Name': 'b', 'Default Value': 2},
            {'Name': 'c', 'Default Value': 3},
        )
        symbol = {}
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_all_named_arguments_no_default_values(self):
        params = ({'Name': 'a'}, {'Name': 'b'}, {'Name': 'c'})
        symbol = {
            'Arguments': (
                {'Name': 'b', 'Value': 2},
                {'Name': 'c', 'Value': 3},
                {'Name': 'a', 'Value': 1},
            )
        }
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_all_named_arguments_and_default_values(self):
        params = ({'Name': 'a', 'Default Value': 1}, {'Name': 'b'}, {'Name': 'c'})
        symbol = {
            'Arguments': ({'Name': 'b', 'Value': 2}, {'Name': 'c', 'Value': 3})
        }
        expected = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))

    def test_only_named_overwrite_default_values(self):
        params = (
            {'Name': 'a', 'Default Value': 101},
            {'Name': 'b', 'Default Value': 102},
        )
        symbol = {
            'Arguments': ({'Name': 'a', 'Value': 1}, {'Name': 'b', 'Value': 2})
        }
        expected = {'a': 1, 'b': 2}
        self.assertEqual(expected, args.resolve_arguments(symbol, params))
