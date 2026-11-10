# Three-AI Memory Path Reference (<项目目录>)

## Actual Memory Locations (verified 2026-05-06)

### 小爱 (Hermes Agent) — WSL

| Item | Path | Type | Size |
|------|------|------|------|
| Memory | `~/.hermes/memories/MEMORY.md` | Plain text | ~3.7 KB |
| User profile | `~/.hermes/memories/USER.md` | Plain text | ~1.6 KB |
| Soul/identity | `~/.hermes/SOUL.md` | Plain text | ~513 B |
| Sessions | `~/.hermes/sessions/*.jsonl` | JSONL | ~38 MB total |
| Skills | `~/.hermes/skills/` | Directory | Variable |
| Config | `~/.hermes/config.yaml` | YAML | ~6 KB |
| Auth | `~/.hermes/.env` + `~/.hermes/auth.json` | Env/JSON | Sensitive |

### 真维斯 (OpenClaw) — Windows

| Item | Path | Type | Size |
|------|------|------|------|
| Memory DB | `%USERPROFILE%\.openclaw\memory\main.sqlite` | SQLite | ~94 KB |
| Memory WAL | `%USERPROFILE%\.openclaw\memory\main.sqlite-wal` | SQLite WAL | ~0 B |
| Memory SHM | `%USERPROFILE%\.openclaw\memory\main.sqlite-shm` | SQLite SHM | ~32 KB |
| Config | `%USERPROFILE%\.openclaw\openclaw.json` | JSON | ~2.4 KB |
| Agents | `%USERPROFILE%\.openclaw\agents\` | Directory | — |
| Workspace | `%USERPROFILE%\.openclaw\workspace\` | Directory | — |

> **⚠️ Critical:** The memory is at `.openclaw\memory\` NOT `.openclaw\agents\main\memory\`. The `agents\main\memory\` path from earlier versions of the install script is WRONG.

### 阿酷 (Claude Code) — Windows

| Item | Path | Type | Size |
|------|------|------|------|
| Conversation history | `%USERPROFILE%\.claude\history.jsonl` | JSONL | ~65 KB |
| Settings | `%USERPROFILE%\.claude\settings.json` | JSON | ~386 B |
| Stats | `%USERPROFILE%\.claude\stats-cache.json` | JSON | ~1 KB |
| Sessions | `%USERPROFILE%\.claude\sessions\` | Directory | Empty |
| Skills | `%USERPROFILE%\.claude\skills\` | Directory | ~35 MB |
| Backups (config only) | `%USERPROFILE%\.claude\backups\*.json.backup.*` | JSON | ~30 KB total |

> **⚠️ Don't export `%USERPROFILE%\.claude\backups\project_backup_*`** — these are full project git repos and can be 568+ MB. Only export the `.json.backup.*` config files.

## Common Mistakes

| Mistake | Consequence |
|---------|-------------|
| `~/.hermes/memory/` (singular) | Memory files not found; agent starts fresh |
| `.openclaw\agents\main\memory\` | Memory SQLite not restored; agent forgets everything |
| Copy entire `.claude\backups\` | 568MB of unnecessary git repos + node_modules on USB |
| Write .ps1 with UTF-8 no BOM | Chinese chars corrupt, PowerShell parser errors |

## Verification Checklist

After export to USB, verify:

```powershell
# Quick size/dir check
Get-ChildItem "E:\<项目目录>备份\记忆存储\" -Recurse -Directory |
  Select-Object FullName,
    @{N='Files';E={(Get-ChildItem $_.FullName -File).Count}},
    @{N='Size(KB)';E={[math]::Round((Get-ChildItem $_.FullName -Recurse -File | Measure-Object Length -Sum).Sum/1KB, 1)}}
```
