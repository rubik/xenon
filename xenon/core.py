from radon.complexity import cc_rank, SCORE
from radon.cli import Config
from radon.cli.harvest import CCHarvester


def av(n, m):
    '''Compute n/m if `m != 0` or otherwise return 0.'''
    return n / m if m != 0 else 0


def check(rank, default=None):
    '''Check whether `rank` is greater than `default`.'''
    return rank > default.upper() if default is not None else False


def analyze(args, logger):
    config = Config(
        exclude=args.exclude,
        ignore=args.ignore,
        order=SCORE,
        no_assert=args.no_assert,
    )
    h = CCHarvester([args.path], config)
    results = h._to_dicts()
    runner = Runner(args, logger)
    return runner.run(results), results


class Runner(object):

    def __init__(self, args, logger):
        self.errors = 0
        self.args = args
        self.logger = logger

    def log(self, msg, *args, **kwargs):
        self.errors += 1
        self.logger.error(msg, *args, **kwargs)

    def run(self, results):
        module_averages = []
        total_cc = 0.
        total_blocks = 0
        for module, blocks in results.items():
            module_cc = 0.
            for block in blocks:
                module_cc += block['complexity']
                r = cc_rank(block['complexity'])
                if check(r, self.args.absolute):
                    self.log('block "%s:%s %s" has a rank of %s', module,
                             block['lineno'], block['name'], r)
            module_averages.append((module, av(module_cc, len(blocks))))
            total_cc += module_cc
            total_blocks += len(blocks)

        ar = cc_rank(av(total_cc, total_blocks))
        if check(ar, self.args.average):
            self.log('average complexity is ranked %s', ar)
        for module, ma in module_averages:
            mar = cc_rank(ma)
            if check(mar, self.args.modules):
                self.log('module %r has a rank of %s', module, mar)
        return self.errors
