'''This module is used to gather all the Git-related data.'''

import os
import sh

FORMAT = '%n'.join(['%H', '%aN', '%ae', '%at', '%cN', '%ce', '%ct', '%s'])


def gitrepo(root):
    '''Construct a dictionary holding all the Git data that can be found.'''
    oldpwd = sh.pwd().strip()
    sh.cd(root)
    gitlog = sh.git('--no-pager', 'log', '-1',
                    pretty="format:%s" % FORMAT).split('\n', 7)
    branch = (os.environ.get('CIRCLE_BRANCH') or
              os.environ.get('TRAVIS_BRANCH',
                             sh.git('rev-parse',
                                    '--abbrev-ref', 'HEAD').strip()))
    remotes = [x.split() for x in sh.git.remote('-v').strip().splitlines()
               if x.endswith('(fetch)')]
    sh.cd(oldpwd)
    return {
        "head": {
            "id": gitlog[0],
            "author_name": gitlog[1],
            "author_email": gitlog[2],
            "author_timestamp": gitlog[3],
            "committer_name": gitlog[4],
            "committer_email": gitlog[5],
            "committer_timestamp": gitlog[6],
            "message": gitlog[7].strip(),
        },
        "branch": branch,
        "remotes": [{'name': r[0], 'url': r[1]} for r in remotes]
    }
