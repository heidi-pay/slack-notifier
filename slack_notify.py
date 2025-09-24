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


def terraform_plan_success(repo_name: AnyStr, pr_number: AnyStr, plan_output: AnyStr, webhook: AnyStr, github_ref: AnyStr):
    template = "/code/terraform_plan_success.json"
    pr_url = "https://github.com/{}/{}/pull/{}".format(REPO_OWNER, repo_name, pr_number)
    commit_url = "https://github.com/{}/{}/commit/{}".format(REPO_OWNER, repo_name, github_ref.split('/')[-1])

    with open(template) as f:
        data = json.load(f)

    # Truncate plan output if too long (Slack has limits)
    truncated_output = plan_output
    if len(plan_output) > 2000:
        truncated_output = plan_output[:1900] + "\n... (truncated, see full output in artifacts)"

    # Extract summary from plan output (look for common terraform plan patterns)
    plan_summary = "Plan completed successfully"
    if "Plan:" in plan_output:
        lines = plan_output.split('\n')
        for line in lines:
            if "Plan:" in line and ("to add" in line or "to change" in line or "to destroy" in line):
                plan_summary = line.strip()
                break

    data = json.dumps(data)

    data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("PR_NUMBER", pr_number) \
        .replace("PLAN_SUMMARY", plan_summary) \
        .replace("PLAN_OUTPUT", truncated_output) \
        .replace("PR_URL", pr_url) \
        .replace("COMMIT_URL", commit_url)

    print(data)

    r = requests.post(webhook,
                      data=json.dumps(json.loads(data)).encode('utf-8'),
                      headers={"Content-type": "application/json"})
    print(r.text)


def terraform_plan_failure(repo_name: AnyStr, pr_number: AnyStr, plan_output: AnyStr, webhook: AnyStr, github_ref: AnyStr):
    template = "/code/terraform_plan_failure.json"
    pr_url = "https://github.com/{}/{}/pull/{}".format(REPO_OWNER, repo_name, pr_number)
    commit_url = "https://github.com/{}/{}/commit/{}".format(REPO_OWNER, repo_name, github_ref.split('/')[-1])

    with open(template) as f:
        data = json.load(f)

    # Truncate error output if too long
    truncated_error = plan_output
    if len(plan_output) > 2000:
        truncated_error = plan_output[:1900] + "\n... (truncated, see full output in artifacts)"

    data = json.dumps(data)

    data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("PR_NUMBER", pr_number) \
        .replace("PLAN_ERROR", truncated_error) \
        .replace("PR_URL", pr_url) \
        .replace("COMMIT_URL", commit_url)

    print(data)

    r = requests.post(webhook,
                      data=json.dumps(json.loads(data)).encode('utf-8'),
                      headers={"Content-type": "application/json"})
    print(r.text)


def main():
    repo_name = sys.argv[1]
    auth_header = sys.argv[2]
    github_ref = sys.argv[3]
    webhook = sys.argv[4]
    outcome = sys.argv[5] if len(sys.argv) > 5 else None
    plan_type = sys.argv[6] if len(sys.argv) > 6 else None
    pr_number = sys.argv[7] if len(sys.argv) > 7 else None
    plan_output = sys.argv[8] if len(sys.argv) > 8 else None

    # Handle Terraform plan notifications
    if plan_type == "terraform-plan":
        if outcome == "true":
            terraform_plan_success(repo_name, pr_number, plan_output, webhook, github_ref)
        elif outcome == "false":
            terraform_plan_failure(repo_name, pr_number, plan_output, webhook, github_ref)
        else:
            # Default to success if outcome not specified
            terraform_plan_success(repo_name, pr_number, plan_output, webhook, github_ref)
    else:
        # Handle release notifications (existing behavior)
        build_number = github_ref.split('/')[2]  # Assumed to be of the form "refs/tags/vX"
        if outcome:
            if outcome == "true":
                release_success(repo_name, auth_header, build_number, webhook)
            if outcome == "false":
                release_failure(repo_name, build_number, webhook)
        else:
            release_success(repo_name, auth_header, build_number, webhook)


if __name__ == "__main__":
    main()