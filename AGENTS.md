# Repository agent rules

## Protected accounts

The human owner has frozen these two account identities:

- `admin@weilan.com` — operator account
- `test@weilan.com` — non-operator test account

Preserve each protected account's email, password hash, role, and database record exactly as found. AI-authored migrations, seeds, tests, debugging scripts, deployments, and data cleanup must use isolated non-protected accounts and must leave these records unchanged. Read-only existence, role, and login verification is allowed.

A protected account may change only when the human owner explicitly requests the exact account change in the current conversation. A general request to fix authentication, reset test data, deploy, seed, migrate, or clean a database is not authorization to change a protected account.

Before completing work that touches authentication, users, seeds, migrations, databases, or production data, verify that no protected account record or credential was mutated. Keep plaintext passwords out of repository files, logs, fixtures, patches, and deployment bundles.
