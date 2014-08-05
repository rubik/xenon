import json
import requests


def post(url, repo_token, service_job_id, service_name, git, cc_data):
    payload = build_payload(repo_token, service_job_id, service_name, git,
                            cc_data)
    return requests.post(url, data=payload)


def build_payload(repo_token, service_job_id, service_name, git, cc_data):
    content = {
        'service_job_id': service_job_id,
        'service_name': service_name,
        'git': git,
        'cc_data': cc_data,
    }
    if repo_token:
        content['repo_token'] = repo_token
    return json.dumps(content)
