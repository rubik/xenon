#import mock  # can't use mock because patches influences each other
import unittest
import collections
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from paramunittest import parametrized

import xenon


Block = collections.namedtuple('Block', 'name complexity lineno')
Args = collections.namedtuple('Args', 'absolute average modules')

def genexp(dict):
    for a, b in dict.items():
        yield a, b


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
        self.assertEqual(xenon.av(self.m, self.n), self.r)


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
        self.assertEqual(xenon.check(self.a, self.b), self.r)


@parametrized(
    # results
    # absolute, average, modules
    # exit code
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'B', 'B'),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('B', 'B', 'B'),
        1
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'A', 'B'),
        1
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'B', 'A'),
        1
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        (None, 'B', 'B'),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', None, 'B'),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        ('C', 'B', None),
        0
    ),
    (
        {'mod.py': [4, 12, 8, 9], 'mod2.py': [3, 3, 2, 10]},
        (None, None, None),
        0
    ),
)
class RunTestCase(unittest.TestCase):

    def setParameters(self, results, args, exit_code):
        r = {}
        for k, v in results.items():
            r[k] = [Block(name='block', complexity=cc, lineno=1) for cc in v]
        self.r = genexp(r)
        self.args = Args(*args)
        self.exit_code = exit_code

    def test_run(self):
        def _log(*args, **kwargs):
            pass
        def _analyze_cc():
            return self.r
        x = xenon.Xenon(self.args)
        x._analyze_cc = _analyze_cc
        xenon.sys.stdout = StringIO()
        self.assertEqual(x.run(), self.exit_code)


if __name__ == '__main__':
    unittest.main()
