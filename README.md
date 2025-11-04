> # Slack Notifier GitHub Action

This action notifies slack of HeidiPay releases and Terraform plan results. 

## Inputs

- `repository-name` - The name of the GitHub repository 
- `github-token` - The GitHub token to access private repositories
- `github-ref` - The release version in the form refs/tags/v4 or commit ref
- `slack-hook` - The URL for the slack hook to request
- `outcome` - The outcome of the job (true/false) - optional
- `notification-type` - The type of notification (release, terraform) - optional
- `pr-number` - The PR number for terraform notifications - optional
- `output` - The terraform output content (supports base64 encoding) - optional
- `action-type` - The terraform action type (PLAN, APPLY, etc.) - optional
- `gcp-environment` - The GCP environment name (e.g., dev, staging, prod) - optional

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
  notification-type: 'terraform'
  pr-number: '123'
  output: 'UGxhbjogMiB0byBhZGQsIDEgdG8gY2hhbmdlLCAwIHRvIGRlc3Ryb3kuLi4='  # base64 encoded
  action-type: 'PLAN'
  gcp-environment: 'dev'
```

### Terraform apply notifications
```
uses: actions/slack-notifier@v3
with:
  repository-name: 'my-repo'
  github-token: 'XXXXXXXXXX'
  github-ref: 'refs/pull/123/merge'
  slack-hook: 'https://hooks.slack.com/services/XXXXX/XXXXX/XXXX'
  outcome: 'true'
  notification-type: 'terraform'
  pr-number: '123'
  output: 'QXBwbHkgY29tcGxldGUhIDIgYWRkZWQsIDEgY2hhbmdlZCwgMCBkZXN0cm95ZWQuLi4='  # base64 encoded
  action-type: 'APPLY'
  gcp-environment: 'prod'
```

**Note:** The `output` parameter supports both plain text and base64-encoded content. The action will automatically detect and decode base64 content.

## Local testing

1. Create a test slack webhook
2. Generate a GitHub Personal Access Token
3. Run the python script in the form:

```bash
python slack_notify.py <repository-name> <github_token> <github-ref> <slack-hook> <repository-owner>
```