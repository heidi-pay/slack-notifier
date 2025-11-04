import base64
import json
import os
import sys
from typing import AnyStr

import requests


REPO_OWNER = "heidi-pay"


def decode_base64_if_needed(text: AnyStr) -> str:
    """
    Decode base64 text if it appears to be base64 encoded, otherwise return as-is.
    """
    if not text:
        return ""

    try:
        # Try to decode as base64
        decoded = base64.b64decode(text).decode('utf-8')
        return decoded
    except Exception:
        # If decoding fails, assume it's plain text
        return text


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


def terraform_success(repo_name: AnyStr, pr_number: AnyStr, output: AnyStr, webhook: AnyStr, github_ref: AnyStr, action_type: str = "PLAN", gcp_environment: str = "", run_id: str = ""):
    template = "/code/terraform_success.json"
    pr_url = "https://github.com/{}/{}/pull/{}".format(REPO_OWNER, repo_name, pr_number)
    
    # Construct run URL from GitHub Run ID
    run_url = ""
    if run_id:
        run_url = "https://github.com/{}/{}/actions/runs/{}".format(REPO_OWNER, repo_name, run_id)

    with open(template) as f:
        data = json.load(f)

    # Decode base64 if needed
    decoded_output = decode_base64_if_needed(output)

    # Truncate output if too long (Slack has limits)
    truncated_output = decoded_output
    if len(decoded_output) > 2000:
        truncated_output = decoded_output[:1900] + "\n... (truncated, see full output in artifacts)"

    # Extract summary from output (look for common terraform patterns)
    summary = f"{action_type} completed successfully"
    if "Plan:" in decoded_output:
        lines = decoded_output.split('\n')
        for line in lines:
            if "Plan:" in line and ("to add" in line or "to change" in line or "to destroy" in line):
                summary = line.strip()
                break
    elif "Apply complete!" in decoded_output:
        summary = "Apply completed successfully"
    elif "Apply:" in decoded_output:
        lines = decoded_output.split('\n')
        for line in lines:
            if "Apply:" in line and ("added" in line or "changed" in line or "destroyed" in line):
                summary = line.strip()
                break

    # Properly escape the output and summary for JSON
    def escape_for_json(text):
        if not text:
            return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

    escaped_tf_action_summary = escape_for_json(summary)
    escaped_tf_action_output = escape_for_json(truncated_output)

    data = json.dumps(data)

    data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("PR_NUMBER", pr_number) \
        .replace("TF_SUMMARY", escaped_tf_action_summary) \
        .replace("TF_OUTPUT", escaped_tf_action_output) \
        .replace("PR_URL", pr_url) \
        .replace("ACTION_TYPE", action_type) \
        .replace("GCP_ENVIRONMENT_NAME", gcp_environment) \
        .replace("RUN_URL", run_url)

    print(data)

    r = requests.post(webhook,
                      data=json.dumps(json.loads(data)).encode('utf-8'),
                      headers={"Content-type": "application/json"})
    print(r.text)


def terraform_failure(repo_name: AnyStr, pr_number: AnyStr, output: AnyStr, webhook: AnyStr, github_ref: AnyStr, action_type: str = "PLAN", gcp_environment: str = "", run_id: str = ""):
    template = "/code/terraform_failure.json"
    pr_url = "https://github.com/{}/{}/pull/{}".format(REPO_OWNER, repo_name, pr_number)
    
    # Construct run URL from GitHub Run ID
    run_url = ""
    if run_id:
        run_url = "https://github.com/{}/{}/actions/runs/{}".format(REPO_OWNER, repo_name, run_id)

    with open(template) as f:
        data = json.load(f)

    # Decode base64 if needed
    decoded_output = decode_base64_if_needed(output)

    # Truncate error output if too long
    truncated_error = decoded_output
    if len(decoded_output) > 2000:
        truncated_error = decoded_output[:1900] + "\n... (truncated, see full output in artifacts)"

    # Properly escape the error output for JSON
    def escape_for_json(text):
        if not text:
            return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

    escaped_error = escape_for_json(truncated_error)

    data = json.dumps(data)

    data = data.replace("REPOSITORY_NAME", repo_name) \
        .replace("PR_NUMBER", pr_number) \
        .replace("TF_ERROR", escaped_error) \
        .replace("PR_URL", pr_url) \
        .replace("ACTION_TYPE", action_type) \
        .replace("GCP_ENVIRONMENT_NAME", gcp_environment) \
        .replace("RUN_URL", run_url)

    print(data)

    r = requests.post(webhook,
                      data=json.dumps(json.loads(data)).encode('utf-8'),
                      headers={"Content-type": "application/json"})
    print(r.text)


def main():
    # Read from environment variables (more reliable than sys.argv)
    repo_name = os.getenv('INPUT_REPOSITORY_NAME', '')
    auth_header = os.getenv('INPUT_GITHUB_TOKEN', '')
    github_ref = os.getenv('INPUT_GITHUB_REF', '')
    webhook = os.getenv('INPUT_SLACK_HOOK', '')
    outcome = os.getenv('INPUT_OUTCOME', 'false')
    notification_type = os.getenv('INPUT_NOTIFICATION_TYPE', '')
    pr_number = os.getenv('INPUT_PR_NUMBER', '')
    output = os.getenv('INPUT_OUTPUT', '')
    action_type = os.getenv('INPUT_ACTION_TYPE', '')
    gcp_environment = os.getenv('INPUT_GCP_ENVIRONMENT', '')
    run_id = os.getenv('INPUT_RUN_ID', '')
    
    # Debug: Show which parameters were read from environment variables
    print(f"[DEBUG] Environment variables read:")
    print(f"[DEBUG]   INPUT_REPOSITORY_NAME: '{repo_name}'")
    print(f"[DEBUG]   INPUT_GITHUB_TOKEN: {'[SET]' if auth_header else '[NOT SET]'}")
    print(f"[DEBUG]   INPUT_GITHUB_REF: '{github_ref}'")
    print(f"[DEBUG]   INPUT_SLACK_HOOK: {'[SET]' if webhook else '[NOT SET]'}")
    print(f"[DEBUG]   INPUT_OUTCOME: '{outcome}'")
    print(f"[DEBUG]   INPUT_NOTIFICATION_TYPE: '{notification_type}'")
    print(f"[DEBUG]   INPUT_PR_NUMBER: '{pr_number}'")
    print(f"[DEBUG]   INPUT_OUTPUT: {'[SET]' if output else '[NOT SET]'}")
    print(f"[DEBUG]   INPUT_ACTION_TYPE: '{action_type}'")
    print(f"[DEBUG]   INPUT_GCP_ENVIRONMENT: '{gcp_environment}'")
    print(f"[DEBUG]   INPUT_RUN_ID: '{run_id}'")
    print(f"[DEBUG] sys.argv length: {len(sys.argv)}")
    if len(sys.argv) > 1:
        print(f"[DEBUG] sys.argv values: {sys.argv[1:]}")
    
    # Fallback to sys.argv for backward compatibility
    if not repo_name and len(sys.argv) > 1:
        repo_name = sys.argv[1]
        print(f"[DEBUG] Using sys.argv fallback for repo_name: {repo_name}")
    if not auth_header and len(sys.argv) > 2:
        auth_header = sys.argv[2]
        print(f"[DEBUG] Using sys.argv fallback for auth_header")
    if not github_ref and len(sys.argv) > 3:
        github_ref = sys.argv[3]
        print(f"[DEBUG] Using sys.argv fallback for github_ref: {github_ref}")
    if not webhook and len(sys.argv) > 4:
        webhook = sys.argv[4]
        print(f"[DEBUG] Using sys.argv fallback for webhook")
    if not outcome and len(sys.argv) > 5:
        outcome = sys.argv[5]
        print(f"[DEBUG] Using sys.argv fallback for outcome: {outcome}")
    if not notification_type and len(sys.argv) > 6:
        notification_type = sys.argv[6]
        print(f"[DEBUG] Using sys.argv fallback for notification_type: {notification_type}")
    if not pr_number and len(sys.argv) > 7:
        pr_number = sys.argv[7]
        print(f"[DEBUG] Using sys.argv fallback for pr_number: {pr_number}")
    if not output and len(sys.argv) > 8:
        output = sys.argv[8]
        print(f"[DEBUG] Using sys.argv fallback for output")
    if not action_type and len(sys.argv) > 9:
        action_type = sys.argv[9]
        print(f"[DEBUG] Using sys.argv fallback for action_type: {action_type}")
    # Default action_type to 'PLAN'
    if not action_type:
        action_type = 'PLAN'
    if not gcp_environment and len(sys.argv) > 10:
        gcp_environment = sys.argv[10]
        print(f"[DEBUG] Using sys.argv fallback for gcp_environment: {gcp_environment}")
    if not run_id and len(sys.argv) > 11:
        run_id = sys.argv[11]
        print(f"[DEBUG] Using sys.argv fallback for run_id: {run_id}")

    # Handle Terraform notifications
    if notification_type == "terraform":
        print(f"[DEBUG] → Using NEW FLOW: Terraform notifications")
        if outcome == "true":
            terraform_success(repo_name, pr_number, output, webhook, github_ref, action_type, gcp_environment, run_id)
        else:
            terraform_failure(repo_name, pr_number, output, webhook, github_ref, action_type, gcp_environment, run_id)
    else:
        print(f"[DEBUG] → Using OLD FLOW: Release notifications")
        print(f"[DEBUG] Release notification inputs:")
        print(f"[DEBUG]   repo_name: '{repo_name}'")
        print(f"[DEBUG]   github_ref: '{github_ref}'")
        print(f"[DEBUG]   outcome: '{outcome}' (type: {type(outcome).__name__})")
        print(f"[DEBUG]   auth_header: {'[SET]' if auth_header else '[NOT SET]'}")
        print(f"[DEBUG]   webhook: {'[SET]' if webhook else '[NOT SET]'}")
        
        # Handle release notifications (existing behavior)
        # Extract build number from github_ref (format: refs/tags/vX or refs/heads/branch)
        try:
            build_number = github_ref.split('/')[2]  # Assumed to be of the form "refs/tags/vX"
            print(f"[DEBUG] Extracted build_number from github_ref '{github_ref}': '{build_number}'")
        except (IndexError, AttributeError) as e:
            print(f"[ERROR] Failed to extract build_number from github_ref '{github_ref}': {e}")
            # Fallback: use the full ref or just the last part
            if github_ref and github_ref.startswith('refs/'):
                build_number = github_ref.replace('refs/', '').replace('/', '-')
            else:
                build_number = github_ref or 'unknown'
            print(f"[DEBUG] Using fallback build_number: '{build_number}'")
        
        print(f"[DEBUG] Final build_number: '{build_number}'")
        print(f"[DEBUG] Outcome comparison: outcome == 'true' → {outcome == 'true'}")
        
        if outcome == "true":
            print(f"[DEBUG] → Calling release_success()")
            release_success(repo_name, auth_header, build_number, webhook)
        else:
            print(f"[DEBUG] → Calling release_failure()")
            release_failure(repo_name, build_number, webhook)

if __name__ == "__main__":
    main()
