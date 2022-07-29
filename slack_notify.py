import json
import sys
from typing import AnyStr

import requests


REPO_OWNER = "heidi-pay"


def release_success(repo_name: AnyStr, auth_header: AnyStr, build_number: AnyStr, webhook: AnyStr):
    template = "/code/release_success.json"
    repo_url = "https://github.com/{}/{}/releases/tag/{}".format(REPO_OWNER, repo_name, build_number)

    r = requests.get("https://api.github.com/repos/{}/{}/releases/latest".format(REPO_OWNER, repo_name),
                     data={},
                     headers={"Authorization": "token {}".format(auth_header)})

    if r.status_code != 200:
        raise RuntimeError("Did not receive 200 back from github API ({} instead)".format(r.status_code))

    if not r or not r.text:
        raise RuntimeError("Did not find any text in github API response")

    json_response = json.loads(r.text, strict=False)

    body = json_response['body']
    body = body \
        .replace('\a', '\\a') \
        .replace('\b', '\\b') \
        .replace('\t', '\\t') \
        .replace('\n', '\\n') \
        .replace('\v', '\\v') \
        .replace('\f', '\\f') \
        .replace('\r', '\\r') \
        .replace("\"", "\\\"")

    with open(template) as f:
        data = json.load(f)

    data = json.dumps(data)

    if body == "":
        body = "No release notes"

    data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("BUILD_NUMBER", build_number) \
        .replace("BODY", body) \
        .replace("REPO_URL", repo_url)

    print(data)

    r = requests.post(webhook,
                      data=json.dumps(json.loads(data)).encode('utf-8'),
                      headers={"Content-type": "application/json"})
    print(r.text)


def release_failure(repo_name: AnyStr, build_number: AnyStr, webhook: AnyStr):
    template = "/code/release_failure.json"
    repo_url = "https://github.com/{}/{}/releases/tag/{}".format(REPO_OWNER, repo_name, build_number)

    with open(template) as f:
        data = json.load(f)

    data = json.dumps(data)

    data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("BUILD_NUMBER", build_number) \
        .replace("REPO_URL", repo_url)

    print(data)

    r = requests.post(webhook,
                      data=json.dumps(json.loads(data)).encode('utf-8'),
                      headers={"Content-type": "application/json"})
    print(r.text)


def main():
    repo_name = sys.argv[1]
    auth_header = sys.argv[2]
    build_number = sys.argv[3].split('/')[2]  # Assumed to be of the form "refs/tags/vX"
    webhook = sys.argv[4]
    outcome = sys.argv[5]

    if outcome:
        if outcome == "true":
            release_success(repo_name, auth_header, build_number, webhook)
        if outcome == "false":
            release_failure(repo_name, build_number, webhook)
    else:
        release_success(repo_name, auth_header, build_number, webhook)


if __name__ == "__main__":
    main()