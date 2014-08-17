# coding=utf-8
# import mock  # can't use mock because patches influences each other
import os
import unittest
import collections

import httpretty
from paramunittest import parametrized

from xenon import core, api, main


Args = collections.namedtuple('Args', 'absolute average modules')


class CatchAll(object):

    def __getattr__(self, attr):
        return lambda *a, **kw: True


class Arguments(object):
    path = 'xenon'
    url = 'http://api.barium.cc/jobs'
    repo_token = 'abcdef1234569abdcef'
    service_job_id = '4699301'
    service_name = 'travis-ci',
    config = os.path.join(path, '.xenon.yml')
    exclude = None
    ignore = None
    no_assert = False
    average = None
    absolute = None
    modules = None


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
            r[k] = [dict(name='block', complexity=cc, lineno=1) for cc in v]
        self.r = r
        self.args = Args(*args)
        self.logger = CatchAll()
        self.exit_code = exit_code

    def test_run(self):
        code = core.find_infractions(self.args, self.logger, self.r)
        self.assertEqual(code != 0, self.exit_code)


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
