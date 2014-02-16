__version__ = '0.1'


def main():
    import sys
    import argparse
    from xenon.core import Xenon

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

    x = Xenon(parser.parse_args())
    sys.exit(x.run())


if __name__ == '__main__':
    main()
