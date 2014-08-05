import os
import sh

FORMAT = '%n'.join(['%H', '%aN', '%ae', '%cN', '%ce', '%s'])


def gitrepo(root):
    oldpwd = sh.pwd().strip()
    sh.cd(root)
    gitlog = sh.git('--no-pager', 'log', '-1',
                    pretty="format:%s" % FORMAT).split('\n', 5)
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
            "committer_name": gitlog[3],
            "committer_email": gitlog[4],
            "message": gitlog[5].strip(),
        },
        "branch": branch,
        "remotes": [{'name': r[0], 'url': r[1]} for r in remotes]
    }
