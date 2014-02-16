import sys
import operator
import argparse

from radon.tools import iter_filenames
from radon.complexity import cc_visit, cc_rank


def av(n, m):
    return n / m if m != 0 else 0


def check(rank, default):
    return rank > default.upper() if default is not None else False


class Xenon(object):

    def __init__(self, args):
        self.args = args
        self.errors = 0

    def log(self, msg, *args, **kwargs):
        self.errors += 1
        sys.stdout.write('xenon: error: {0}\n'.format(msg.format(*args,
                                                                 **kwargs)))

    def _analyze_cc(self):
        import radon
        print radon.__version__
        import inspect
        print inspect.getsource(iter_filenames)
        for name in iter_filenames(self.args.path, self.args.exclude,
                                   self.args.ignore):
            with open(name) as fobj:
                yield name, cc_visit(fobj.read(),
                                     no_assert=self.args.no_assert)

    def run(self):
        module_averages = []
        total_cc = 0.
        total_blocks = 0
        for module, results in self._analyze_cc():
            module_cc = 0.
            for block in results:
                module_cc += block.complexity
                r = cc_rank(block.complexity)
                if check(r, self.args.absolute):
                    self.log('block "{0}:{1} {2}" has a rank of {3}', module,
                             block.lineno, block.name, r)
            module_averages.append((module, av(module_cc, len(results))))
            total_cc += module_cc
            total_blocks += len(results)

        ar = cc_rank(av(total_cc, total_blocks))
        if check(ar, self.args.average):
            self.log('average complexity is ranked {0}', ar)
        for module, ma in module_averages:
            mar = cc_rank(ma)
            if check(mar, self.args.modules):
                self.log('module "{0}" has a rank of {1}', module, mar)

        return self.errors
