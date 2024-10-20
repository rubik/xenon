# coding=utf-8
# import mock  # can't use mock because patches influences each other
import os
import sys
import unittest
import unittest.mock
import collections
import tempfile
import sys
import argparse

# Monkey-patch paramunittest for Python 3.10+
if sys.version_info[:2] >= (3, 10):
    import collections.abc
    collections.Mapping = collections.abc.Mapping

import httpretty
from paramunittest import parametrized

import xenon
from xenon import core, api, main


Args = collections.namedtuple('Args', 'absolute average modules averagenum')


class CatchAll(object):

    def __getattr__(self, attr):
        return lambda *a, **kw: True


class Arguments(object):
    path = ['xenon']
    url = 'http://api.barium.cc/jobs'
    repo_token = 'abcdef1234569abdcef'
    service_job_id = '4699301'
    service_name = 'travis-ci',
    config = os.path.join(path[0], '.xenon.yml')
    exclude = None
    ignore = None
    no_assert = False
    average = None
    absolute = None
    modules = None
    averagenum = None


@parametrized(
    (20, 10, 2),
    (0, 10, 0),
    (0, 0, 0),
)
class AvTestCase(unittest.TestCase):

    def setParameters(self, m, n, r):
        self.m = m
        self.n = n
        self.r = r

    def testAv(self):
        self.assertEqual(core.av(self.m, self.n), self.r)


@parametrized(
    ('A', 'A', False),
    ('B', 'A', True),
    ('C', None, False),
    ('A', None, False),
    ('A', 'a', False),
    ('B', 'a', True),
)
class CheckTestCase(unittest.TestCase):

    def setParameters(self, a, b, r):
        self.a = a
        self.b = b
        self.r = r

    def testCheck(self):
        self.assertEqual(core.check(self.a, self.b), self.r)


@parametrized(
    # results
    # absolute, average, modules, averagenum
    # infractions
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'B', 'B', None),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('B', 'B', 'B', None),
        1
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'A', 'B', None),
        1
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'B', 'A', None),
        1
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        (None, 'B', 'B', None),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', None, 'B', None),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'B', None, None),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        (None, None, None, 0),
        1
    ),
)
class InfractionsTestCase(unittest.TestCase):

    def setParameters(self, results, args, infractions):
        r = {}
        for k, v in results.items():
            r[k] = [dict(name='block', complexity=cc, lineno=1) for cc in v]
        self.r = r
        self.args = Args(*args)
        self.logger = CatchAll()
        self.infractions = infractions

    def test_run(self):
        infr = core.find_infractions(self.args, self.logger, self.r)
        self.assertEqual(infr, self.infractions)


class APITestCase(unittest.TestCase):

    def _exit_code(self):
        try:
            main(Arguments)
        except SystemExit as e:
            return e.code

    @httpretty.activate
    def test_main_ok(self):
        httpretty.register_uri(
            httpretty.POST,
            'http://api.barium.cc/jobs',
            body='{"message":"Job #5.1","url":"http://barium.cc/jobs/5722"}'
        )
        self.assertEqual(self._exit_code(), 0)

    @httpretty.activate
    def test_main_not_ok(self):
        httpretty.register_uri(
            httpretty.POST,
            'http://api.barium.cc/jobs',
            body='{"message":"Build processing error.","error":true,"url":""}',
            status=500,
        )
        self.assertEqual(self._exit_code(), 3)

    @httpretty.activate
    def test_api(self):
        httpretty.register_uri(
            httpretty.POST,
            'http://api.barium.cc/jobs',
            body='{"message":"Resource creation started",'
                 '"url":"http://barium.cc/jobs/5722"}'
        )
        response = api.post(
            url=Arguments.url,
            repo_token=Arguments.repo_token,
            service_job_id=Arguments.service_job_id,
            service_name=Arguments.service_name,
            git={},
            cc_data={}
        )
        self.assertEqual(response.json(),
                         {'url': 'http://barium.cc/jobs/5722',
                          'message': 'Resource creation started'})


class TestCustomConfigParserGetStr(unittest.TestCase):
    '''Test class for class CustomConfigParser - getstr method.'''

    @staticmethod
    def get_configuration(text):
        '''Get CustomConfigParser object with loaded text.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(text)

            configuration = xenon.CustomConfigParser()
            configuration.read(pyproject_path)

        return configuration

    def test_missing_section_case(self):
        '''Test missing section case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", "path_3"]\n'
            'max_average = "A"\n'
            'max_average_num = 1.2\n')

        self.assertEqual(
            configuration.getstr(xenon.PYPROJECT_SECTION, "maxaverage", "None"), "None")

    def test_with_trim_value_case(self):
        '''Test with trim value case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", "path_3"]\n'
            'max_average = "A"\n'
            'max_modules = \'B\'\n'
            'max_average_num = 1.2\n')

        self.assertEqual(
            configuration.getstr(xenon.PYPROJECT_SECTION, "max_average", "None"), "A")

        self.assertEqual(
            configuration.getstr(xenon.PYPROJECT_SECTION, "max_modules", "None"), "B")

    def test_without_trim_value_case(self):
        '''Test without trim value case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", "path_3"]\n'
            'max_average = A\n'
            'max_average-num = 1.2\n')

        self.assertEqual(
            configuration.getstr(xenon.PYPROJECT_SECTION, "max_average", "None"), "A")


class TestCustomConfigParserGetListStr(unittest.TestCase):
    '''Test class for class CustomConfigParser - getliststr method.'''

    @staticmethod
    def get_configuration(text):
        '''Get CustomConfigParser object with loaded text.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(text)

            configuration = xenon.CustomConfigParser()
            configuration.read(pyproject_path)

        return configuration

    def test_missing_section_case(self):
        '''Test missing section case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", "path_3"]\n'
            'max_average = "A"\n'
            'max_average-num = 1.2\n')

        self.assertEqual(
            configuration.getliststr(xenon.PYPROJECT_SECTION, "maxaverage", "None"), "None")

    def test_parse_error_case(self):
        '''Test parse error case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", "path_3"\n'
            'max_average = "A"\n'
            'max_average-num = 1.2\n')

        self.assertRaisesRegex(
            xenon.PyProjectParseError, "path", configuration.getliststr,
            xenon.PYPROJECT_SECTION, "path")

    def test_single_value_case(self):
        '''Test single value case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = "path_1"\n'
            'max_average = "A"\n'
            'max_average-num = 1.2\n')

        self.assertListEqual(
            configuration.getliststr(xenon.PYPROJECT_SECTION, "path", None), ["path_1"])

    def test_invalid_format_case(self):
        '''Test invalid format case'''
        # Not a list case
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = {"path_1": "path_2"}\n'
            'max_average = "A"\n'
            'max_average-num = 1.2\n')

        self.assertRaisesRegex(
            xenon.PyProjectParseError, "path", configuration.getliststr,
            xenon.PYPROJECT_SECTION, "path", None)

        # Not a list of str case
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", true]\n'
            'max_average = "A"\n'
            'max_average-num = 1.2\n')

        self.assertRaisesRegex(
            xenon.PyProjectParseError, "path", configuration.getliststr,
            xenon.PYPROJECT_SECTION, "path", None)

    def test_multiple_values_case(self):
        '''Test multiple values case.'''
        configuration = self.get_configuration(
            '[tool.xenon]\n'
            'path = ["path_1", "path_2", "path_3"]\n'
            'max_average = "A"\n'
            'max_average-num = 1.2\n')

        self.assertListEqual(
            configuration.getliststr(xenon.PYPROJECT_SECTION, "path", None),
            ["path_1", "path_2", "path_3"])


class TestParsePyproject(unittest.TestCase):
    '''Test class for function parse_pyproject.'''

    def test_parse_error_case(self):
        '''Parse error case.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write('parameter = value')

            self.assertRaisesRegex(
                xenon.PyProjectParseError, "Unable", xenon.parse_pyproject, pyproject_path)

    def test_duplicate_parameteres_case(self):
        '''Test duplicate parameters case'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(
                    '[tool.xenon]\n'
                    'max_average_num = value_1\n'
                    'max_average_num = value_2')

            self.assertRaisesRegex(
                xenon.PyProjectParseError, "duplicate parameters", xenon.parse_pyproject, pyproject_path)

    def test_missing_file_case(self):
        '''Test missing file path case.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertDictEqual(xenon.parse_pyproject(tmp_dir), {})

    def test_invalid_max_average_num_type_case(self):
        '''Test invalid max-average-num parameter type case'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write('[tool.xenon]\nmax_average_num = value')

            self.assertRaisesRegex(
                xenon.PyProjectParseError, "max_average_num", xenon.parse_pyproject, pyproject_path)

    def test_invalid_no_assert_type_case(self):
        '''Test invalid no_assert parameter type case'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write('[tool.xenon]\nno_assert = next')

            self.assertRaisesRegex(
                xenon.PyProjectParseError, "no_assert", xenon.parse_pyproject, pyproject_path)

    def test_all_parameters_case(self):
        '''Test all parameters case.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(
                    '[tool.xenon]\n'
                    'path = ["path_1", "path_2", "path_3"]\n'
                    'max_average = "A"\n'
                    'max_average_num = 1.2\n'
                    'max_modules = "B"\n'
                    'max_absolute = "C"\n'
                    'exclude = ["path_4", "path_5"]\n'
                    'ignore = ["path_6", "path_7"]\n'
                    'no_assert = true')

            result = xenon.parse_pyproject(pyproject_path)

            self.assertDictEqual(
                xenon.parse_pyproject(pyproject_path), {
                    "path": ["path_1", "path_2", "path_3"],
                    "average": 'A',
                    "averagenum": 1.2,
                    "modules": 'B',
                    "absolute": 'C',
                    "url": None,
                    "config": None,
                    "exclude": 'path_4,path_5',
                    "ignore": 'path_6,path_7',
                    "no_assert": True})


class TestGetParserDefaultsAndDeleteDefaults(unittest.TestCase):
    '''Test class for function get_parser_defaults_and_delete_defaults.'''

    def test_valid_case(self):
        '''Test valid case'''
        parser = argparse.ArgumentParser(add_help=False)

        parser.add_argument("-t", "--test", default="test")
        parser.add_argument("-v", "--values", default="values", dest="val")
        parser.add_argument("-w", "--without")

        args_defualt = xenon.get_parser_defaults_and_delete_defaults(parser)

        self.assertEqual(args_defualt, {"test": "test", "val": "values"})

        sys.argv = ["file.py"]

        parser.parse_args()

        self.assertEqual(
            vars(parser.parse_args()), {"test": None, "val": None, "without": None})


class TestParseArgs(unittest.TestCase):
    '''Test class for function parse_args.'''

    def test_cmd_pyproject_case(self):
        '''Test parameter set from cmd and pyproject case.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(
                    '[tool.xenon]\n'
                    'max_average = "A"\n')

            sys.argv = ["file", "-a", "B"]

            args = xenon.parse_args(pyproject_path)
            self.assertEqual(args.average, "B")

    def test_cmd_default_value_case(self):
        '''Test parameter not set from cmd (with default value) and pyproject case.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(
                    '[tool.xenon]\n'
                    'config_file = config_file_path\n')

            sys.argv = ["file"]

            args = xenon.parse_args(pyproject_path)
            self.assertEqual(args.config, "config_file_path")

    def test_cmd_non_default_value_case(self):
        '''Test parameter set from cmd (with default value) and pyproject case.'''
        with tempfile.TemporaryDirectory() as tmp_dir:
            pyproject_path = tmp_dir + '/pyproject.toml'
            with open(pyproject_path, "w") as toml_file:
                toml_file.write(
                    '[tool.xenon]\n'
                    'config_file = config_file_path\n')

            # Set different value in cmd then default
            sys.argv = ["file", "--config-file", "cfg_file_path"]

            args = xenon.parse_args(pyproject_path)
            self.assertEqual(args.config, "cfg_file_path")

            # Set same value in cmd as default
            sys.argv = ["file", "--config-file", ".xenon.yml"]

            args = xenon.parse_args(pyproject_path)
            self.assertEqual(args.config, ".xenon.yml")


if __name__ == '__main__':
    unittest.main()
