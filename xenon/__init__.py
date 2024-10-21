'''Module containing the two topmost-level functions: parse_args() and main().
The latter is the entry point for the command line program.
'''

__version__ = '0.9.3'

import os
import sys
import logging


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
    parser.add_argument('--paths-in-front', dest='paths_in_front', action='store_true',
                        help='Print block and module complexity with log line starting with their path')

    args = parser.parse_args()
    # normalize the rank
    for attr in ('absolute', 'modules', 'average'):
        val = getattr(args, attr, None)
        if val is None:
            continue
        setattr(args, attr, val.upper())
    try:
        with open(args.config, 'r') as f:
            yml = yaml.safe_load(f)
    except (getattr(__builtins__, 'FileNotFoundError', IOError),
            yaml.YAMLError):
        yml = {}
    args.repo_token = yml.get('repo_token',
                              os.environ.get('BARIUM_REPO_TOKEN', ''))
    args.service_name = yml.get('service_name', 'travis-ci')
    args.service_job_id = os.environ.get('TRAVIS_JOB_ID', '')
    return args


def main(args=None):
    '''Entry point for the command line program. ``sys.exit`` is called at the
    end.
    '''
    from xenon.api import post
    from xenon.core import analyze
    from xenon.repository import gitrepo

    args = args or parse_args()
    if args.paths_in_front:
        # Skip the level and module name to have log line starting with message
        # When using xenon in PyCharm terminal, one can benefit from
        # PyCharm changing path to the violation location into the active link
        logging.basicConfig(level=logging.INFO, format='%(message)s')
    else:
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
