# coding=utf-8
# import mock  # can't use mock because patches influences each other
import os
import sys
import unittest
import collections

if sys.version_info[:2] >= (3, 10):
    import collections.abc
    collections.Mapping = collections.abc.Mapping

import httpretty
from paramunittest import parametrized

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


if __name__ == '__main__':
    unittest.main()
