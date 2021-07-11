'''Module containing the two topmost-level functions: parse_args() and main().
The latter is the entry point for the command line program.
'''

__version__ = '0.7.3'

import os
import sys
import logging
import json


# Import ConfigParser based on python version
if sys.version_info[0] == 2:
    import ConfigParser as configparser
else:
    import configparser

PYPROJECT_SECTION = "tool.xenon"


class PyProjectParseError(Exception):
    '''Exception for pyproject.toml parser.'''
    def __init__(self, msg) -> None:
        super(PyProjectParseError, self).__init__(msg)


class CustomConfigParser(configparser.ConfigParser):
    '''Custom ConfigParser.'''

    def getstr(self, section, option, fallback=object()):
        '''Get required option which is strings'''
        values = self.get(section, option, fallback=fallback)
        if values == fallback:
            return fallback

        # Trim " or '
        if (values[0] == '"' and values[-1] == '"') or (values[0] == '\'' and values[-1] == '\''):
            return values[1:-1]

        return values

    def getliststr(self, section, option, fallback=object()):
        '''Get required option which is list of strings.'''
        values = self.get(section, option, fallback=fallback)
        if values == fallback:
            return fallback

        # Conver string to python object
        try:
            values = json.loads(values)
        except json.decoder.JSONDecodeError:
            raise PyProjectParseError("Invalid format of parameter %s" % option)

        # Single parameter
        if isinstance(values, str):
            return [values]

        # Check format - list
        if not isinstance(values, list):
            raise PyProjectParseError("Invalid format of parameter %s" % option)

        # Check items
        for value in values:
            if not isinstance(value, str):
                raise PyProjectParseError("Invalid format of parameter %s" % option)

        return values


def parse_pyproject(file_path):
    '''Parse pyproject.toml file.'''
    pyproject_parameters = {}

    configuration = CustomConfigParser()

    # Invalid format - missing any section []
    try:
        loaded_files = configuration.read(file_path)
    except configparser.MissingSectionHeaderError:
        raise PyProjectParseError("Unable to parse %s" %file_path)
    except configparser.DuplicateOptionError:
        raise PyProjectParseError("%s contain duplicate parameters" %file_path)

    # Pyproject.toml does not exists
    if not loaded_files:
        return pyproject_parameters

    # Parse single string values
    for parameter in (("max-average", "average"),
                      ("max-modules", "modules"),
                      ("max-absolute", "absolute"),
                      ("url", "url"),
                      ("config-file", "config")):
        pyproject_parameters[parameter[1]] = configuration.getstr(
            PYPROJECT_SECTION, parameter[0], fallback=None)

    # Parse list of string to str
    for parameter in (("exclude", "exclude"), ("ignore", "ignore")):
        values = configuration.getliststr(PYPROJECT_SECTION, parameter[0], None)
        if values:
            pyproject_parameters[parameter[1]] = ",".join(values)
        else:
            pyproject_parameters[parameter[1]] = None

    # Parse list of string as list
    pyproject_parameters["path"] = configuration.getliststr(
        PYPROJECT_SECTION, "path", fallback=None)

    try:
        pyproject_parameters["averagenum"] = configuration.getfloat(
            PYPROJECT_SECTION, "max-average-num", fallback=None)
    except ValueError:
        raise PyProjectParseError("Invalid format of parameter max-average-num")

    try:
        pyproject_parameters["no_assert"] = configuration.getboolean(
            PYPROJECT_SECTION, "no-assert", fallback=None)
    except ValueError:
        raise PyProjectParseError("Invalid format of parameter no-assert")

    return pyproject_parameters


def parse_args():
    '''Parse arguments from the command line and read the config file (for the
    REPO_TOKEN value).
    '''
    import yaml
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                        version=__version__)
    parser.add_argument('path', help='Directory containing source files to '
                        'analyze, or multiple file paths', nargs='+')
    parser.add_argument('-a', '--max-average', dest='average', metavar='<str>',
                        help='Letter grade threshold for the average complexity')
    parser.add_argument('--max-average-num', dest='averagenum', type=float,
                        help='Numeric threshold for the average complexity')
    parser.add_argument('-m', '--max-modules', dest='modules', metavar='<str>',
                        help='Threshold for modules complexity')
    parser.add_argument('-b', '--max-absolute', dest='absolute',
                        metavar='<str>', help='Absolute threshold for block '
                        'complexity')
    parser.add_argument('-e', '--exclude', metavar='<str>', dest='exclude',
                        help='Comma separated list of patterns to exclude')
    parser.add_argument('-i', '--ignore', metavar='<str>', dest='ignore',
                        help='Comma separated list of patterns to ignore. If '
                        'they are directories, Xenon won\'t even descend into '
                        'them')
    parser.add_argument('-u', '--url', metavar='<URL>', dest='url',
                        help='Where to send the JSON data through a POST '
                        'request.')
    parser.add_argument('--no-assert', dest='no_assert', action='store_true',
                        help='Do not count `assert` statements when computing '
                        'complexity')
    parser.add_argument('-c', '--config-file', metavar='<path>', dest='config',
                        default='.xenon.yml', help='Xenon config file '
                        '(default: %(default)s)')

    args = parser.parse_args()
    # normalize the rank
    for attr in ('absolute', 'modules', 'average'):
        val = getattr(args, attr, None)
        if val is None:
            continue
        setattr(args, attr, val.upper())
    try:
        with open(args.config, 'r') as f:
            yml = yaml.load(f)
    except (getattr(__builtins__, 'FileNotFoundError', IOError),
            yaml.YAMLError):
        yml = {}
    args.repo_token = yml.get('repo_token',
                              os.environ.get('BARIUM_REPO_TOKEN', ''))
    args.service_name = yml.get('service_name', 'travis-ci')
    args.service_job_id = os.environ.get('TRAVIS_JOB_ID', '')

    pyproject_args = parse_pyproject("pyproject.toml")

    # Include args from pyproject.toml file
    for arg_name, arg_value in pyproject_args.items():
        if arg_value:
            setattr(args, arg_name, arg_value)

    return args


def main(args=None):
    '''Entry point for the command line program. ``sys.exit`` is called at the
    end.
    '''
    from xenon.api import post
    from xenon.core import analyze
    from xenon.repository import gitrepo

    args = args or parse_args()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('xenon')
    if args.url and len(args.path) > 1:
        logger.error(
            '-u, --url cannot be used when multiple paths are specified',
        )
        sys.exit(1)
    errors, cc_data = analyze(args, logger)
    exit_code = 0
    if args.url:
        response = post(
            url=args.url,
            repo_token=args.repo_token,
            service_job_id=args.service_job_id,
            service_name=args.service_name,
            git=gitrepo(args.path[0]),
            cc_data=cc_data
        )
        logger.info('HTTP: %s', response.status_code)
        logger.info('HTTP: %s', response.text)
        if 'error' in response.json():
            exit_code = 3
    if errors:
        exit_code = 1
    sys.exit(exit_code)
