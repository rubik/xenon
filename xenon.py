import sys
import operator
import argparse

from radon.tools import iter_filenames
from radon.complexity import cc_visit, cc_rank

__version__ = '0.1'


INFO = {
    'errors': False,
}

def log(msg, *args, **kwargs):
    INFO['errors'] = True
    sys.stdout.write('xenon: {}\n'.format(msg.format(*args, **kwargs)))


def av(n, m):
    return n / m if m != 0 else 0


def check(rank, default):
    return rank > default.upper() if default is not None else False


def analyze_cc(args):
    for name in iter_filenames(args.path, args.exclude, args.ignore):
        with open(name) as fobj:
            yield name, cc_visit(fobj.read(), no_assert=args.no_assert)


def run(args):
    module_averages = []
    total_cc = 0.
    total_blocks = 0
    for module, results in analyze_cc(args):
        module_cc = 0.
        for block in results:
            module_cc += block.complexity
            r = cc_rank(block.complexity)
            if check(r, args.absolute):
                log('error: block {} in module {} has a rank of {}',
                    block.name, module, r)
        module_averages.append((module, av(module_cc, len(results))))
        total_cc += module_cc
        total_blocks += len(results)

    ar = cc_rank(av(total_cc, total_blocks))
    if check(ar, args.average):
        log('error: average complexity has a rank of {}', ar)
    for module, ma in module_averages:
        mar = cc_rank(ma)
        if check(mar, args.modules):
            log('error: module {} has a rank of {}', module, mar)

    sys.exit(INFO['errors'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                        version=__version__)
    parser.add_argument('path', nargs='+', help='Source files to analyze')
    parser.add_argument('-a', '--max-average', dest='average', metavar='<str>',
                        help='Threshold for the average complexity')
    parser.add_argument('-m', '--max-modules', dest='modules', metavar='<str>',
                        help='Threshold for modules complexity')
    parser.add_argument('-b', '--max-absolute', dest='absolute',
                        metavar='<str>', help='Absolute threshold for block '
                        'complexity')
    parser.add_argument('-e', '--exclude', metavar='<str>', dest='exclude',
                        help='Comma separated list of patters to exclude')
    parser.add_argument('-i', '--ignore', metavar='<str>', dest='ignore',
                        help='Comma separated list of patters to ignore. If '
                        'they are directories, xenon won\'t even descend into '
                        'them')
    parser.add_argument('--no-assert', metavar='<str>', dest='no_assert',
                        help='Do not count `assert` statements when computing '
                        'complexity')

    run(parser.parse_args())
