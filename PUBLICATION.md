# Publication handoff

The audit release is complete locally, but the configured GitHub integration can
read the `khurramidris` account and cannot create a new repository. GitHub returned
`Resource not accessible by integration` for the creation request on 2026-10-23.
No remote was added and no partial repository exists.

The account owner needs to do one account-side step:

1. Create an empty **public** repository named `smallville-plus` under
   `khurramidris` at <https://github.com/new>. Do not initialize it with a README,
   license, or `.gitignore`.
2. Grant the connected GitHub integration write access to that repository if the
   installation asks for repository selection.
3. Resume this task. The prepared history, tag, topics, security settings, and
   release can then be pushed and verified without further design decisions.

The intended URL is <https://github.com/khurramidris/smallville-plus>. Until it
exists, `dist/smallville-plus-audit-r2-source.tar.gz` is the tracked source
snapshot and `dist/smallville-plus-audit-r2.git.bundle` is a cloneable copy of
the full Git history. Both are generated locally after the final audit commit and
are ignored by Git.

An auditor can clone the bundle with:

```bash
git clone smallville-plus-audit-r2.git.bundle smallville-plus
cd smallville-plus
git checkout audit-r2-2026-10-23
```
