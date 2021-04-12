import json
import requests
import os
import sys

repo_name= sys.argv[1]
auth_header= sys.argv[2]
build_number=sys.argv[3].split('/')[2] # Assumed to be of the form "refs/tags/vX"
template="slack_release_template.json"
webhook=sys.argv[4]

repo_url="https://github.com/heidi-pay/{}/releases/tag/{}".format(repo_name, build_number)

r = requests.get("https://api.github.com/repos/heidi-pay/{}/releases/latest".format(repo_name), 
        data={}, 
        headers={"Authorization": "token {}".format(auth_header)})

json_response = json.loads(r.text, strict=False)
body = json_response['body']
body = body.replace('\n', '\\n').replace('\r', '\\r')

with open(template) as f:
        data = json.load(f)

data = json.dumps(data)

data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("BUILD_NUMBER", build_number) \
        .replace("BODY", body) \
        .replace("REPO_URL", repo_url)

r = requests.post(webhook,
        data=json.dumps(json.loads(data)).encode('utf-8'), 
                headers={"Content-type": "application/json"})
