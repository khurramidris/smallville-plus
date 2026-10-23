# Public audit release

The complete tracked project and Git history are public at
<https://github.com/khurramidris/smallville-plus>. Anonymous retrieval of the
`main` branch was checked against the local file bytes after the first push.

The stable snapshot is `audit-r2-2026-10-23`. Its GitHub release contains:

- `smallville-plus-audit-r2-source.tar.gz`, containing every tracked file;
- `smallville-plus-audit-r2.git.bundle`, containing the complete Git history;
- `manifest.json`, recording the tag, commit, sizes, hashes and verification; and
- `SHA256SUMS`, covering all three artifacts.

Local copies remain under ignored `dist/`. The 14 GB generated `runs/` tree is
not source and is not published; the deterministic commands in `AUDIT.md`
regenerate it, while compact research evidence is tracked under `reports/`.

An auditor can clone the bundle with:

```bash
git clone smallville-plus-audit-r2.git.bundle smallville-plus
cd smallville-plus
git checkout audit-r2-2026-10-23
```

## Account-owner settings

The connected integration can push code and releases but GitHub rejects repository
metadata and security-setting changes with `Resource not accessible by
integration`. The account owner can optionally finish these settings in the web
interface:

1. Add the description: “Research town simulation with authoritative world
   rules, bounded cognition, economy, social processes, replay, and offline
   evaluation.”
2. Add topics: `agent-based-modeling`, `generative-agents`,
   `multi-agent-systems`, `simulation`, `research`, and `python`.
3. Disable the unused wiki and projects features.
4. Enable private vulnerability reporting under **Settings → Code security**.
