import json
import sys

import requests

repo_name = sys.argv[1]
auth_header = sys.argv[2]
build_number = sys.argv[3].split('/')[2]  # Assumed to be of the form "refs/tags/vX"
template = "/code/slack_release_template.json"
webhook = sys.argv[4]
repo_owner = "heidi-pay"

repo_url = "https://github.com/{}/{}/releases/tag/{}".format(repo_owner, repo_name, build_number)

r = requests.get("https://api.github.com/repos/{}/{}/releases/latest".format(repo_owner, repo_name),
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
