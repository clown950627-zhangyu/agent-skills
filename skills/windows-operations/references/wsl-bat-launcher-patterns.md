# WSL .bat Launcher Patterns — Reference

## The Problem

Windows CMD interprets `|`, `&&`, `&`, `>`, `<` as its own operators even inside double-quoted `wsl.exe bash -c "..."` strings. This causes compound commands to be split before bash ever sees them.

## The Solution: Shell Script + `wsl bash ~/script.sh`

Create a bash script in the WSL home directory, then call it from the bat file.

### WSL Side — Gateway Launcher (`~/hermes-gateway.sh`)
```bash
#!/bin/bash
cd ~/.hermes/hermes-agent || { echo "[错误] Hermes 目录不存在"; exit 1; }
source venv/bin/activate || { echo "[错误] 虚拟环境激活失败"; exit 1; }
echo "[信息] 正在启动 Hermes 网关 (QQ Bot)..."
echo "[信息] 时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
exec python -m hermes_cli.main gateway run --replace
```

### WSL Side — CLI Launcher (`~/hermes-cli.sh`)
```bash
#!/bin/bash
cd ~/.hermes/hermes-agent || { echo "[错误] Hermes 目录不存在"; exit 1; }
source venv/bin/activate || { echo "[错误] 虚拟环境激活失败"; exit 1; }
echo "[信息] 正在连接小爱..."
echo "[提示] 直接输入文字对话，输入 /exit 退出"
echo ""
exec python cli.py
```

### Windows Side — Gateway Bat (`启动Hermes网关.bat`)
```bat
@echo off
title Hermes 网关 - QQ Bot
chcp 65001 >nul
color 0A

echo ╔═══════════════════════════════════════════╗
echo ║        小爱 Hermes 网关启动程序            ║
echo ╚═══════════════════════════════════════════╝
echo.

:: 检查WSL是否可用
wsl echo "WSL就绪" >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] WSL未启动，正在尝试启动...
    wsl -d Ubuntu
    timeout /t 5 /nobreak >nul
)

echo [信息] 正在启动 Hermes 网关（QQ Bot）...
wsl bash ~/hermes-gateway.sh

echo.
echo [提示] 网关已停止。按任意键关闭...
pause >nul
```

### Windows Side — CLI Bat (`小爱命令行.bat`)
```bat
@echo off
title 小爱 Hermes 命令行
chcp 65001 >nul
color 0B

echo ╔═══════════════════════════════════════════╗
echo ║     小爱 Hermes 智能助手 - 命令行         ║
echo ╚═══════════════════════════════════════════╝
echo.
echo [信息] 正在连接小爱...
wsl bash ~/hermes-cli.sh

echo.
echo [信息] 小爱已离线，按任意键关闭...
pause >nul
```

## Variants: ~ vs Absolute Paths

The form `wsl bash ~/script.sh` relies on bash expanding `~` to the WSL home directory. In some environments, this may fail. **More robust variants:**

### Absolute WSL Path (Recommended for Reliability)
```bat
C:\Windows\System32\wsl.exe -e /bin/bash /home/clown_zy/hermes-gateway.sh
```

Advantages over `~` form:
- No shell expansion needed — path is explicit
- `-e` flag bypasses WSL's default shell logic
- Full `System32` path avoids PATH dependency
- Works even if WSL default distro changes

### Using `wsl ~` (Newer WSL)
```bat
wsl ~ -e /bin/bash ~/hermes-gateway.sh
```
The `~` flag tells WSL to start in home directory, separate from bash `~` expansion.

## Diagnostic Test Pattern

When a .bat file fails with no visible error, create a simple test:

**WSL side (`~/hermes-test.sh`):**
```bash
#!/bin/bash
echo "[测试] 脚本被成功调用" > <C盘>/Users/username/Desktop/wsl_test_result.txt
echo "[测试] WSL用户: $(whoami)" >> <C盘>/Users/username/Desktop/wsl_test_result.txt
echo "[测试] 主目录: $HOME" >> <C盘>/Users/username/Desktop/wsl_test_result.txt
echo "[测试] 时间: $(date)" >> <C盘>/Users/username/Desktop/wsl_test_result.txt
```

**Windows side (`WSL测试.bat`):**
```bat
@echo off
echo [测试1] 检查WSL...
wsl echo "OK" >nul 2>&1
if %errorlevel% equ 0 (echo [通过] WSL可用) else (echo [失败] WSL不可用 & pause & exit /b)

echo [测试2] 执行测试脚本...
wsl -e /bin/bash /home/clown_zy/hermes-test.sh
if %errorlevel% equ 0 (echo [通过] 脚本已执行) else (echo [失败] 脚本执行失败)
pause
```

The script writes to the Windows desktop, making the output visible regardless of whether CMD displays it correctly.

## Verification

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Permission denied` | Script not executable | `chmod +x ~/hermes-*.sh` |
| Hermes目录不存在 | WSL path mismatch | Check `~/.hermes/hermes-agent/` exists |
| 虚拟环境激活失败 | Wrong venv path | Check `venv/` vs `.venv/` — actual path is `venv/` |
| Window closes immediately | No `pause` in bat | Add `pause >nul` at end |
| `wsl: command not found` or errorlevel≠0 | `wsl.exe` not in PATH or WSL not installed | Use full path `C:\Windows\System32\wsl.exe` in bat |
