# ToggleMaster GitOps Rules

- This repository is the deployment source of truth; it contains no service source or Terraform.
- Never commit passwords, tokens, private keys, kubeconfigs, Vault contents, or rendered Secrets.
- Image tags must use immutable sha-<12 hex> values after publication is enabled.
- Keep one overlay per service so promotions remain independent.
- Shared namespace and platform resources must have one owner.
- Automated sync stays disabled until the user explicitly authorizes deployment readiness.
- Never run kubectl apply, Argo sync, Helm, or cluster mutations without explicit authorization.
- Never add Co-Authored-By lines to commit messages.
