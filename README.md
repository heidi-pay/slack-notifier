> # Slack Notifier GitHub Action

This action notifies slack of HeidiPay releases and Terraform plan results. 

## Inputs

- `repository-name` - The name of the GitHub repository 
- `github-token` - The GitHub token to access private repositories
- `github-ref` - The release version in the form refs/tags/v4 or commit ref
- `slack-hook` - The URL for the slack hook to request
- `outcome` - The outcome of the job (true/false) - optional
- `plan-type` - The type of notification (release, terraform-plan) - optional
- `pr-number` - The PR number for terraform plan notifications - optional
- `plan-output` - The terraform plan output content (supports base64 encoding) - optional

## Outputs

None

## Example usage

### Release notifications
```
uses: actions/slack-notifier@v3
with:
  repository-name: 'gh-actions'
  github-token: 'XXXXXXXXXX'
  github-ref: 'refs/tags/v4'
  slack-hook: 'https://hooks.slack.com/services/XXXXX/XXXXX/XXXX'
  outcome: 'true'
```

### Terraform plan notifications
```
uses: actions/slack-notifier@v3
with:
  repository-name: 'my-repo'
  github-token: 'XXXXXXXXXX'
  github-ref: 'refs/pull/123/merge'
  slack-hook: 'https://hooks.slack.com/services/XXXXX/XXXXX/XXXX'
  outcome: 'true'
  plan-type: 'terraform-plan'
  pr-number: '123'
  plan-output: 'UGxhbjogMiB0byBhZGQsIDEgdG8gY2hhbmdlLCAwIHRvIGRlc3Ryb3kuLi4='  # base64 encoded
```

**Note:** The `plan-output` parameter supports both plain text and base64-encoded content. The action will automatically detect and decode base64 content.

## Local testing

1. Create a test slack webhook
2. Generate a GitHub Personal Access Token
3. Run the python script in the form:

```bash
python slack_notify.py <repository-name> <github_token> <github-ref> <slack-hook> <repository-owner>
```