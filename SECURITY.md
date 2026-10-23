# Security policy

Security fixes are applied to the default branch and the most recent audit
snapshot when a backport is practical. This is a research prototype, not a
hosted service with a compatibility or support guarantee.

When the repository owner has enabled it, report a sensitive finding through
GitHub's private vulnerability reporting:

<https://github.com/khurramidris/smallville-plus/security/advisories/new>

The publication integration could not enable this account-level setting. Until
the link accepts reports, do not include live API keys, private model responses,
personal data, or an exploitable proof in a public issue. For non-sensitive
correctness and reproducibility findings, use a public GitHub issue.

The FastAPI viewer is designed for local, read-only researcher inspection and
does not implement authentication or authorization. Do not bind it to an
untrusted network. Live model access is optional; inject provider credentials
only through the process environment and never place them in source, `.env`
files committed to Git, command arguments, reports, or issue content.
