'''This module contains some helper functions to communicate with an API.'''

import json
import requests


def post(url, repo_token, service_job_id, service_name, git, cc_data):
    '''Send a POST request to the specified url.

    *repo_token* is the repository token. It can be ``None``.
    *service_job_id* is the CI's job id.
    *service_name* is the name of the service on which the script is running.
    *git* is a dictionary containing Git-related data.
    *cc_data* is the actual CC data.
    '''
    payload = build_payload(repo_token, service_job_id, service_name, git,
                            cc_data)
    return requests.post(url, data=payload)


def build_payload(repo_token, service_job_id, service_name, git, cc_data):
    '''Construct a payload from the given data.'''
    content = {
        'service_job_id': service_job_id,
        'service_name': service_name,
        'git': git,
        'cc_data': cc_data,
    }
    if repo_token is not None:
        content['repo_token'] = repo_token
    return json.dumps(content)
