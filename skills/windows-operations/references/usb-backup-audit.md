# USB Backup Audit & Completeness Check

After exporting to USB, run an audit to verify everything is in order.

## What to Check

| Check | Tool | Pass/Fail Signal |
|-------|------|-----------------|
| Empty directories | `find . -type d -empty` | Zero empty dirs = pass |
| File count | `find . -type f \| wc -l` | Match expected count |
| Script file existence | Manual check per script | All key scripts present |
| Hardcoded paths | `grep -rn "D:"` on install scripts | Only fallback logic, not hardcoded |
| Memory data | Check 记忆存储/* for files | Must have actual files, not empty dirs |

## Audit Script (Batch)

```batch
@echo off
chcp 65001 >nul
set USB=E:\<项目目录>备份
set SRC=D:\<项目目录>

:: 1. Find empty directories
echo === Empty Dirs ===
for /d /r "%USB%" %%d in (*) do (
    dir /b /a "%%d" 2>nul | findstr . >nul
    if errorlevel 1 echo     [EMPTY] %%d
)

:: 2. Verify key scripts
for %%f in (
    "系统核心\安装包\install.ps1"
    "系统核心\安装包\一键安装.bat"
    "系统核心\安装包\test-install.ps1"
    "安全\健康检查\healthcheck.ps1"
    "系统核心\脚本\小爱备份.sh"
    "系统核心\脚本\每日备份.ps1"
) do if exist "%USB%\%%~f" (echo [OK] %%~f) else (echo [MISSING] %%~f)

:: 3. Check for hardcoded paths in install.ps1
findstr /n "D:" "%USB%\系统核心\安装包\install.ps1" | findstr /v "D:\\\s*$"

:: 4. Compare against source
for /f "delims=" %%f in ('dir /s /b /a-d "%SRC%" ^| findstr /v "node_modules\\obj\\bin\\Release"') do (
    set "rel=%%f" & set "rel=!rel:%SRC%=!"
    if not exist "%USB%\!rel!" echo [MISSING on USB] !rel!
)
```

## Common Issues & Fixes

### Issue 1: Memory dirs empty
The AI memories (小爱/真维斯/阿酷) live in their respective system directories, NOT under `<项目目录>`. The export must pull from:

```
小爱:  WSL  ~/.hermes/memory/  →  D:\<项目目录>\记忆存储\小爱\
真维斯: Windows %USERPROFILE%\.openclaw\agents\main\memory\  →  D:\<项目目录>\记忆存储\真维斯\
阿酷:  Windows %USERPROFILE%\.claude\history.jsonl  →  D:\<项目目录>\记忆存储\阿酷\
```

**Fix:** Run the Windows-side backup script first (`每日备份.ps1`), then export to USB.

### Issue 2: Side projects missing from backup
Projects like `A股筛选系统`, `voice-chat`, `进销存APP`, `项目二*` live as top-level dirs under `<项目目录>` but not under `<项目目录>`. The export must explicitly copy them.

**Fix:** Use `xcopy` with explicit paths for all known project directories:

```batch
xcopy "%SRC%\A股筛选系统\*" "%USB%\项目文件\A股筛选系统\" /E /I /Y /Q >nul
xcopy "%SRC%\voice-chat\*" "%USB%\项目文件\voice-chat\" /E /I /Y /Q >nul
xcopy "%SRC%\进销存APP\*" "%USB%\项目文件\进销存APP\" /E /I /Y /Q >nul
for /d %%d in ("%SRC%\项目二*") do xcopy "%%d\*" "%USB%\项目文件\%%~nxd\" /E /I /Y /Q >nul
```

### Issue 3: node_modules/obj/bin bloat
node_modules, obj/, bin/Release directories are massive (thousands of files) and mostly cache/build artifacts. For a restore USB, they can be skipped or included with the understanding they'll inflate transfer time.

**Trade-off:** Include for completeness (~100MB), exclude for speed (~1MB without).

### Issue 4: Batch file encoding
Windows batch files need CRLF line endings. WSL write_file produces LF.

**Fix:**
```bash
sed -i 's/$/\r/' <D盘>/script.bat
```
