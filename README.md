> # Slack Notifier GitHub Action

This action notifies slack of a HeidiPay release. 

## Inputs

- `repository-name` - The name of the GitHub repository 
- `github-token` - The GitHub token to access private repositories
- `github-ref` - The release version in the form refs/tags/v4

## Outputs

None

## Example usage
```
uses: actions/slack-notifier@v1
with:
  repository-name: 'gh-actions'
  github-token: 'XXXXXXXXXX'
  github-ref: 'refs/tags/v4'
```