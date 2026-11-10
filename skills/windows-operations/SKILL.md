---
name: windows-operations
description: Operate on the Windows host from within WSL — screenshot capture, process management, file system access, and PowerShell invocation. Covers the Hybrid WSL+Windows environment pattern common in local development setups.
tags:
  - windows
  - wsl
  - screenshot
  - powershell
  - devops
  - backup
  - hermes-backup
---

# Windows Operations from WSL

## Overview

When running inside WSL, the Windows host filesystem is mounted at `<C盘>/`, `<D盘>/`, etc. Windows executables live at `<C盘>/Windows/System32/`. This skill covers common patterns for reaching back into Windows from the WSL context.

---

## 1. File System Access

### Mount Points
| Windows Path | WSL Equivalent |
|---|---|
| `C:\...` | `<C盘>/...` |
| `D:\...` | `<D盘>/...` |

### ⚠️ Chinese Filenames — Python via <C盘>/ is the Only Reliable Approach

**This is the #1 gotcha of WSL+Windows operations.** Chinese filenames (common on Chinese Windows) cause failures at every level of PowerShell-based approaches:

| Approach | Problem |
|----------|---------|
| **Inline PowerShell `-Command`** | Chinese chars garbled passing through WSL bash's pipe |
| **UTF-16LE .ps1 script** | Encoding works for display but **hashtable key matching fails** — `$files.Keys` never matches actual filenames |
| **Python subprocess** | Same encoding pipe problem as inline PowerShell |

**✅ The ONLY reliable approach: use Python directly via WSL's `<C盘>/` path.**

```python
import os, shutil

desktop = "<C盘>/Users/<用户名>/Desktop"
# os.listdir() correctly reads Chinese filenames from WSL
files = os.listdir(desktop)
for f in files:
    if f.endswith(".xlsx"):
        shutil.move(
            os.path.join(desktop, f),
            f"<D盘>/目标目录/{f}"
        )
```

**Why this works:** WSL's drvfs mount (`<C盘>/`, `<D盘>/`) preserves UTF-8 natively. Python's `os.listdir()` and `shutil.move()` operate at the kernel level — no encoding pipe, no PowerShell parsing, no hashtable key corruption. **Always default to this approach for any file operation involving Chinese characters.**

**When Python via <C盘>/ isn't possible** (e.g., target is a removable drive E: not mounted in WSL, or you need Registry/Service operations), fall back to PowerShell with UTF-16LE scripts written via Python. For moves/copies with Chinese paths that fail in PowerShell, fall back to a two-step: stage via `<C盘>/` temp, then use PowerShell with ASCII-only paths.

### ⚠️ Write Permission Gotcha
Writing directly to `<C盘>/` from WSL may fail with **Permission denied** because the Windows filesystem is mounted with restrictive permissions. Workarounds:
- Write to WSL's native `/tmp/` or `~/.hermes/` first, then copy via `cp`
- Or run PowerShell to write from the Windows side (use `[System.IO.Path]::GetTempPath()`)

### Copying Files Between Environments
```bash
# WSL → Windows temp
cp /tmp/myfile.png <C盘>/Users/$(whoami)/AppData/Local/Temp/

# Windows temp → WSL
cp <C盘>/Users/username/AppData/Local/Temp/myfile.png /tmp/
```

### Copying Files to Removable Drives (USB)

External USB drives (e.g., E:) cannot be directly mounted from WSL without sudo (requires password). The reliable approach is to script from the Windows side.

**Preferred approach — Batch file with xcopy:**
1. Write a `.bat` file from Python (for correct UTF-8 encoding) to the WSL-accessible D: drive
2. Convert line endings to CRLF via `sed -i 's/$/\r/'`
3. Run via cmd.exe from WSL

```bash
# Write batch with Python for reliable encoding
python3 -c "
content = '''@echo off
chcp 65001 >nul
xcopy \\\"D:\\\\source\\\\*\\\" \\\"E:\\\\dest\\\\\\\" /E /I /Y /Q >nul
echo Done!
pause
'''
with open('<D盘>/export.bat', 'w', encoding='utf-8') as f:
    f.write(content)
"
# Fix line endings
sed -i 's/$/\\r/' <D盘>/export.bat

# Execute from WSL (UNC path warning is harmless)
<C盘>/Windows/System32/cmd.exe /c "D: && D:\\export.bat" 2>&1
```

**xcopy flags explained:**
| Flag | Purpose |
|------|---------|
| `/E` | Copy directories and subdirectories, including empty ones |
| `/I` | Assume destination is a directory if multiple files |
| `/Y` | Suppress overwrite confirmation |
| `/Q` | Quiet mode (no file-by-file listing) |

---

## 2. Running Windows Commands

### PowerShell
```bash
# Basic inline command
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "Write-Host 'hello'"

# With execution policy bypass (scripts)
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "..."
```

### PowerShell Encoding Pitfall (Chinese Content)

Writing `.ps1` files from WSL's write_file to <D盘>/ creates UTF-8 without BOM. Windows PowerShell misparses Chinese characters from such files — multi-byte sequences corrupt surrounding syntax.

**Always prefer Python via `<C盘>/` paths** for any file operation involving Chinese characters (see §1 above). PowerShell is for non-file operations: processes, services, registry, screenshots.

**Never hardcode a Chinese user path inside a `.ps1`.** A script written by `write_file` is UTF-8 without BOM; PowerShell 5.1 reads it as ANSI, so `C:\Users\用户\AppData\Local` becomes mojibake and the whole script dies with `PathNotFound ... ItemNotFoundException` on a path that clearly exists. Symptom is easy to misread as "the app isn't installed". Use the environment instead of the literal:

```powershell
$env:LOCALAPPDATA      # C:\Users\<user>\AppData\Local
$env:USERPROFILE       # C:\Users\<user>
[Environment]::GetFolderPath("Desktop")
$env:APPDATA           # ...\Roaming
```

Need a Chinese **output name** (a shortcut, a file)? Build it from code points so the script stays pure ASCII:

```powershell
$name = [string][char]0x526A + [char]0x6620 + [char]0x4E13 + [char]0x4E1A + [char]0x7248   # 剪映专业版
```

Same rule for `-Command` one-liners: `$` gets eaten by bash first, so escape it or (better) put the logic in a `.ps1` and call it with `-File`.

### ⚠️ `Invoke-RestMethod` 把无 charset 的 JSON 按 Latin-1 解 → 中文全乱码

症状：调本地服务 API（mihomo/clash `/proxies`、HA `/states`、任何自建接口）时，返回里的中文名变成 `å\x8f¯å\x9b½` 这类两字节垃圾；`-like "*美国*"` 永远匹配不上，看起来像「接口里没有这个节点/实体」。接口明明是 200。

根因：PS 5.1 的 `Invoke-RestMethod` 在响应头不带 `charset` 时按 ISO-8859-1 解码。**这与 `.ps1` 文件的 BOM 问题是两层，可以同时踩。**

修法：一律读原始字节显式按 UTF-8 解，请求体也用字节数组。

```powershell
function Get-Json([string]$url) {
    $resp  = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
    $bytes = $resp.RawContentStream.ToArray()
    $txt   = [System.Text.Encoding]::UTF8.GetString($bytes)
    return $txt | ConvertFrom-Json
}

function Put-Json([string]$url, [string]$json) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    Invoke-RestMethod -Uri $url -Method Put -Body $bytes `
        -ContentType "application/json; charset=utf-8" -TimeoutSec 6 | Out-Null
}
```

请求体含中文（`{"name":"美国1"}`）时**必须传字节数组**：传字符串会按 ANSI 编码发出，服务端收到乱码名，切换/写入静默失败或返回 400。

排查顺序：怀疑「中文名匹配不上」时，先把接口返回的名字连同码点 dump 到文件确认，不要先改匹配逻辑。写盘用 `Out-File -Encoding UTF8`（出 BOM），Python 读回用 `encoding='utf-8-sig'`。

**PowerShell workarounds (only when Python <C盘>/ isn't possible, e.g., Registry operations):**
1. **Write via Python** — Use `open(path, 'w', encoding='utf-8')` in Python for reliable UTF-8 output with correct Chinese characters. This worked reliably in testing.
2. **Write via PowerShell** — Pipe content through PowerShell's Out-File with -Encoding UTF8
3. **Write UTF-16LE via Python** — ⚠️ **UTF-16LE fixes display encoding but DOES NOT fix hashtable key matching.** Chinese keys in PowerShell hashtables (e.g., `@{"中文名" = "值"}`) will NOT match because encoding corruption happens at the parser level. **Use numbered arrays instead:**
   ```powershell
   # WRONG — hashtable keys fail to match:
   $files = @{"示例品牌文件.xlsx" = "D:\target\"}
   
   # CORRECT — use parallel arrays:
   $srcPaths = @("C:\Desktop\示例品牌文件.xlsx")
   $dstPaths = @("D:\target\")
   for ($i = 0; $i -lt $srcPaths.Length; $i++) {
       Move-Item $srcPaths[$i] $dstPaths[$i] -Force
   }
   ```
4. **Unicode escapes** — Use `[char]0xXXXX` instead of literal Chinese chars inside the script
5. **Batch file instead** — For copy/file-ops tasks, write a `.bat` file with `chcp 65001` (UTF-8 code page). Batch files with UTF-8 Chinese text work reliably when saved with CRLF line endings.

### PowerShell `$env:VARIABLE` Expansion From WSL Bash

When passing PowerShell commands containing `$env:VARIABLE` from WSL bash, **the `$` is interpreted by bash first**, corrupting the path:

```bash
# WRONG — bash expands $env:USERPROFILE as a bash variable (empty)
powershell.exe -NoProfile -Command "Copy-Item \"$env:USERPROFILE\\.claude\\*\" \"E:\\target\\\""
# PowerShell actually sees: Copy-Item "\\.claude\\*" "E:\\target\\"
```

**Root cause:** bash sees `$env` and looks for a bash variable named `env` (which doesn't exist), evaluates to empty.

**Workarounds:**
1. **Use `[Environment]::GetFolderPath()`** — avoids `$env:` entirely:
   ```bash
   powershell.exe -NoProfile -Command \
     "Copy-Item \"$([Environment]::GetFolderPath('UserProfile'))\\.claude\\*\" \"E:\\target\\\""
   ```
2. **Use Python subprocess with shell=False** — avoids bash escaping
3. **Temp Directory Bridge** — copy via <C盘>/ first, then PowerShell with literal paths

### Temp Directory Bridge Pattern (WSL ↔ Windows)

When WSL cannot directly access a Windows path (e.g., USB drive E: not mounted in WSL, or `\\wsl.localhost\` UNC path fails), use the Windows temp directory as a staging area:

```
# WSL → Temp → Windows Target
WSL file  →  <C盘>/Users/<user>/AppData/Local/Temp/  →  PowerShell Copy-Item to target
```

**Why this works:** `<C盘>/` is always accessible from WSL via the drvfs mount, and `C:\Users\<user>\AppData\Local\Temp\` is always writable from PowerShell.

**Pattern:**
```bash
# Step 1: Copy from WSL to temp (WSL writes to <C盘>/Users/...)
cp ~/.hermes/memories/* <C盘>/Users/<用户名>/AppData/Local/Temp/hermes_mem_backup/

# Step 2: Copy from temp to target (PowerShell handles Windows-side paths)
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command \
  "Copy-Item 'C:\\Users\\<用户名>\\AppData\\Local\\Temp\\hermes_mem_backup\\*' 'E:\\target\\' -Recurse -Force"
```

**Limitation of `\\wsl.localhost\Ubuntu\` UNC path:**
- Works from PowerShell IF the WSL network discovery service is running and the path is accessible
- Fails if WSL hasn't been accessed recently or after system reboot
- Can be slow/timing out for large batch copies
- More reliable to stage through C:\temp as shown above

### Python to Write Correctly-Encoded PowerShell Scripts

For complex multi-line PowerShell scripts that must not suffer encoding corruption:

```python
import subprocess

ps_content = '''
$dst = 'E:\\target\\path'
New-Item $dst -ItemType Directory -Force | Out-Null
foreach ($d in @('sessions','skills')) {
    $p = "$env:USERPROFILE\\.claude\\$d"
    if (Test-Path $p) { Copy-Item $p $dst -Recurse -Force }
}
Write-Host ('Done: ' + (Get-ChildItem $dst -Recurse).Count + ' items')
'''

# Write as UTF-16LE with BOM (PowerShell native encoding)
path = '<C盘>/Users/username/AppData/Local/Temp/script.ps1'
with open(path, 'w', encoding='utf-16le') as f:
    f.write('\ufeff' + ps_content)

# Execute
subprocess.run([
    '<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', 'C:\\Users\\username\\AppData\\Local\\Temp\\script.ps1'
], timeout=60)
```

**When to use UTF-16LE:** Only when the script contains literal Chinese characters AND PowerShell fails to parse the UTF-8 version. For simple commands without Chinese text, UTF-8 (no BOM) is fine when executed via Python's subprocess.

### Batch File (.bat) CRLF Requirement

Windows `.bat` files **must** have CRLF (`\r\n`) line endings. WSL `write_file` produces LF endings, which causes cmd.exe to fail parsing.

**Fix:**
```bash
sed -i 's/$/\r/' <D盘>/script.bat
```

**Running from WSL:**
```bash
# UNC path warning is harmless — prepend drive letter
<C盘>/Windows/System32/cmd.exe /c "D: && D:\\script.bat" 2>&1
```

The `2>&1` redirect captures the UNC path warning (stderr) but the actual command still runs successfully.

### CMD
```bash
<C盘>/Windows/System32/cmd.exe /c "dir C:\"
```

### ⚠️ Windows 可执行文件从 WSL 调用的路径格式

当从 WSL 调用 Windows 原生可执行文件（如 `node.exe`、`python.exe` 等）并传入模块/脚本路径时，必须使用 **Windows 原生路径格式**（`C:\Users\...`），而非 WSL 的 `<C盘>/...` 格式。

```bash
# ❌ 失败 — Windows node 将 <C盘>/... 解析为 UNC 路径
<C盘>/Program\ Files/nodejs/node.exe <C盘>/Users/<用户名>/AppData/Roaming/npm/node_modules/openclaw/dist/index.js --version
# → Error: Cannot find module '\\wsl.localhost\\Ubuntu\\mnt\\c\\Users\\...'

# ✅ 正确 — 使用 Windows 原生路径（即使在 WSL 中调用）
<C盘>/Program\ Files/nodejs/node.exe "C:\Users\<用户名>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" --version
```

**原因：** Windows 的 Node.js/Python 等运行时在解析模块路径时，会将 `<C盘>/...` 转换为 `\\wsl.localhost\\Ubuntu\\mnt\\c\\...`。这个 UNC 路径在 Windows 的模块解析系统中不存在，导致 `MODULE_NOT_FOUND`。

**通用规则：**
| 场景 | 正确格式 | 错误格式 |
|------|---------|---------|
| 可执行文件本身 | `<C盘>/Program\ Files/nodejs/node.exe` | — |
| 传给可执行文件的参数路径 | `"C:\Users\...\script.js"` | `<C盘>/Users/.../script.js` |
| PowerShell `-File` 参数 | `"C:\Users\...\script.ps1"` | `<C盘>/Users/.../script.ps1` |

### Process Checking
```bash
# Check if a Windows process is running
<C盘>/Windows/System32/tasklist.exe /FI "IMAGENAME eq claude.exe" /NH
```

---

## 3. Screenshot Capture

### Problem
.NET's `Screen.Bounds` returns the **scaled (logical) resolution** on high-DPI displays (e.g., 1500x1000 at 200% scaling), not the physical resolution (e.g., 3000x2000). Capturing at the scaled resolution only captures 1/4 of the screen.

### Solution — Full-Resolution Single-Monitor Screenshot

This PowerShell script captures the **entire primary display at physical resolution**, works around the DPI scaling:

```powershell
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Native {
    [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr hWnd);
    [DllImport("gdi32.dll")] public static extern int GetDeviceCaps(IntPtr hdc, int nIndex);
    public const int HORZRES = 8;
    public const int VERTRES = 10;
    public const int DESKTOPHORZRES = 118;
    public const int DESKTOPVERTRES = 117;
}
'@

$hdc = [Native]::GetDC([IntPtr]::Zero)
$realW = [Native]::GetDeviceCaps($hdc, [Native]::DESKTOPHORZRES)
$realH = [Native]::GetDeviceCaps($hdc, [Native]::DESKTOPVERTRES)

$f = New-Object System.Windows.Forms.Form
$f.WindowState = 'Minimized'
$f.Show()
[System.Windows.Forms.Application]::DoEvents()
Start-Sleep -Milliseconds 300

$bmp = New-Object System.Drawing.Bitmap ($realW), ($realH)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(0, 0, 0, 0, [System.Drawing.Size]::new($realW, $realH))
$path = [System.IO.Path]::GetTempPath() + 'screenshot.png'
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $f.Close()
Write-Host ('Saved: ' + $path + ' ' + $realW + 'x' + $realH)
```

### Multi-Monitor Full Desktop
For capturing across ALL monitors, iterate `[System.Windows.Forms.Screen]::AllScreens`, compute the bounding box of all screens, and use that as the CopyFromScreen rect.

### 抓指定窗口（不受前台锁影响）——验收隐藏启动的 GUI 必用

用 `wscript + -WindowStyle Hidden` 启动的 WinForms/WPF 工具，控制台隐藏但窗体仍在，常被其它窗口盖住；`SetForegroundWindow` 被前台锁静默拒绝，整屏截图里永远看不到它，看起来像「没启动」。不要抢前台，直接抓那个窗口自己的位图：

```powershell
# EnumWindows 找标题含 ASCII 片段的可见窗口 → GetWindowRect → PrintWindow
$hdc = $g.GetHdc()
[Cap]::PrintWindow($target, $hdc, 2) | Out-Null   # flags=2 = PW_RENDERFULLCONTENT
$g.ReleaseHdc($hdc); $bmp.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
```

- **`flags` 必须传 `2`**（PW_RENDERFULLCONTENT）；传 `0` 常常只得到黑图，尤其 Chromium 壳 / DirectComposition 界面。
- 抓完直接 `vision_analyze` 读界面文案，等于「不看屏幕也能验收 GUI」：按钮齐不齐、列表是不是空、中文有没有乱码，一眼看完。
- 窗口必须真存在。先用 `EnumWindows + GetWindowText + IsWindowVisible` 列出可见窗口、匹配 **ASCII 标题片段**（中文标题经 WSL 管道是乱码）；列不到就是没起来，先排语法错：
  ```powershell
  $e=$null; [System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw $ps1), [ref]$e) | Out-Null
  if ($e.Count) { $e | % { $_.Message + ' @line ' + $_.Token.StartLine } } else { 'SYNTAX OK' }
  ```
  这个只解析不执行，能在不弹任何窗口的情况下区分「脚本语法错」和「窗口被盖住」——这两者从外部看完全一样，但修法完全不同。

### Sending Screenshot to User
After capturing to Windows temp, copy to `/tmp/` in WSL and use the `MEDIA:` tag:
```bash
cp <C盘>/Users/username/AppData/Local/Temp/screenshot.png /tmp/
# Then in response: MEDIA:/tmp/screenshot.png
```

---

## 4. Process Management
### Check if a Windows Process is Running

```bash
<C盘>/Windows/System32/tasklist.exe /FI "IMAGENAME eq processname.exe" /NH
```

The output will be in Chinese on Chinese Windows. Look for the process name in the output.

### List Processes Matching a Pattern

```bash
<C盘>/Windows/System32/tasklist.exe /NH | grep -i "pattern"
```

### Activate a Window by PID

To bring a running app's window to the foreground:

```bash
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command \
  "[Microsoft.VisualBasic.Interaction]::AppActivate(8736); Write-Host 'DONE'"
```

Works for most apps with visible windows. ⚠️ Does NOT work for system-tray-only apps.

### 把窗口调到前台：`AppActivate` 比 `SetForegroundWindow` 管用

Windows 的前台锁会**静默拒绝** `SetForegroundWindow`（不报错、返回 True，窗口仍然在下面）。UWP/Store 应用（ChatGPT 桌面版这种）尤其如此。

**可靠顺序**：

```powershell
$ws = New-Object -ComObject WScript.Shell
$ok = $ws.AppActivate('ChatGPT')        # 按窗口标题片段激活，返回 True 通常就真的到前台了
if (-not $ok) { Get-Process QQ | ? { $_.MainWindowHandle -ne 0 } | % { $_.CloseMainWindow() }
                Start-Sleep 2; $ws.AppActivate('ChatGPT') }
```

- 标题传**ASCII 片段**（`ChatGPT`），中文标题经 WSL 管道是乱码。
- 激活后**必须截图确认**，不能拿返回值当结论。
- 调不到就先关/最小化压在它上面的窗口，再 `AppActivate`。

### UWP/Store 应用报「加载不了账号」先查系统代理，不要重装

ChatGPT 桌面版显示 `ChatGPT hit a snag — We couldn't load your account` 时，九成是**系统代理被关了**，不是账号或安装坏了。

诊断三步（30 秒）：

```powershell
# ① 系统代理开关与地址
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyEnable
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyServer
# ② 代理进程在不在、端口有没有人听
Get-Process | ? { $_.ProcessName -match 'clash|mihomo|v2ray|sing' } | Select ProcessName,Id
Get-NetTCPConnection -LocalPort 7890 -State Listen
# ③ 从 Windows 侧真跑一次（WSL 侧的 curl 不能作为依据）
try { (Invoke-WebRequest 'https://chatgpt.com' -Proxy 'http://127.0.0.1:7890' -TimeoutSec 15 -UseBasicParsing).StatusCode } catch { $_.Exception.Message }
```

修复：`ProxyEnable=1` + `ProxyServer=127.0.0.1:7890`，然后点应用里的 **Retry**（或重启应用），十几秒就进主界面。

### 界面里冒出 JSON 错误体（`{"detail":"Bad Request"}`）＝ 服务端拒收请求体，按这个顺序排除

ChatGPT/Codex 桌面版在消息气泡位置直接显示 `{"detail":"Bad Request"}` 时，是后端 400，
**不是断网、不是没登录、也不是额度用完**（那三种的报错文案完全不同）。排除顺序，从最便宜的开始：

```
① 换出口节点（美国1 → 美国2/3，或换掉当前机场）—— 节点被风控/链路被改时，请求体会被拒
② 开一个新对话，发一句最简单的「你好」
     新对话能回 → 这个长对话的上下文炸了（跑十几小时、塞满图片），救不回来，只能新开重说
     新对话也 400 → 客户端版本 / 模型名服务端不认，换模型或重装
③ 最后才怀疑账号状态
```

判断前先看它有没有在动：`Working for X 分` 计时在走 + 进程 CPU 有增量 = 在重试，不是死界面；
同一格画面连续两轮完全一致才叫卡死。别把「它在重连」报成「它崩了」。

**要点：代理进程在跑 ≠ 系统代理开着。** `mihomo` 监听 7890 时 `ProxyEnable` 仍可能是 `0`，走系统代理的应用（Store 应用、UWP、Electron 壳）全部连不上，而命令行带 `-x` 的 curl 却是通的——别被后者误导。

### ⚠️ System Tray Apps (No Visible Window)

Some modern apps (Weixin/WeChat, QQ, UWP apps) start as **system tray processes** with NO visible window at all. `Start-Process` launches them successfully but no GUI window exists to activate.

**Signs:**
- `tasklist` shows the process running
- `AppActivate` returns "DONE" but nothing changes on screen
- Screenshot shows the app's icon in the taskbar but no login window

**What to do:**
1. **Kill and restart** — sometimes a fresh launch forces the login window:
   ```bash
   Stop-Process -Name "Weixin" -Force
   Start-Process 'C:\Program Files\Tencent\Weixin\Weixin.exe'
   ```
2. **Tell the user** — the app is running (icon visible in taskbar) and needs a manual click to bring up the window. From WSL you CANNOT force a system-tray app to show its window.
3. **Verify with screenshot** — use `vision_analyze` to confirm the expected window actually appeared before telling the user it's ready.

### Launching Apps That Require Interactive Login (Launch → Verify → Handoff)

"帮我打开 X 并登录" is a recurring request class (QQ, WeChat, DingTalk...). The agent can complete everything EXCEPT the credential step:

1. **Locate & launch** (§8) → confirm the process is running (§4)
2. **Wait 5–10s** — QQ NT / WeChat need time to render the login window; screenshotting too early shows only the desktop
3. **Screenshot** (§3) → `vision_analyze` to determine the window state:
   - Quick-login with saved account (single blue 登录 button) → tell user to click it (optionally tick 自动登录 first)
   - QR code → user must scan with their phone (photo-of-screen QR does NOT work — see Pitfalls)
   - Password form → hand off to user
4. **Hand off explicitly** — describe exactly what is on screen and the ONE action the user must take. Never claim login succeeded without a post-login screenshot showing the main window.

**Never type credentials yourself** — password/2FA entry is a user-confirmation action by policy. You *can* drive the rest of the UI (see §4.1): picking an account the browser already has a session for, pressing 继续, clearing onboarding dialogs. The moment a password or code field appears, hand off.

**QQ NT process signature:** after a successful launch, `tasklist` shows 3–5 `QQ.exe` processes (main + renderer helpers). Multiple processes are NORMAL — not a launch failure.

📍 Session detail: `references/qq-launch-login.md`

### 4.1 Clicking the Windows GUI from WSL (it works — be disciplined)

Mouse injection IS available: `SetCursorPos` + `mouse_event` via PowerShell.

```powershell
Add-Type @"
using System; using System.Runtime.InteropServices;
public class M {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, int e);
}
"@
[M]::SetCursorPos(512, 355); Start-Sleep -Milliseconds 250
[M]::mouse_event(0x02,0,0,0,0); Start-Sleep -Milliseconds 80; [M]::mouse_event(0x04,0,0,0,0)
```

Same pixel space as the screenshot: capture → read the target's position off the
image → click → **screenshot again immediately**.

**Preflight before any multi-step click sequence (30 seconds, saves 15 turns).**
Click one known control — a dropdown, a nav row, the search box — and screenshot.
If nothing changed, do NOT re-aim the same coordinates; the input path is broken,
not the geometry. Diagnose in this order:

1. **Resolution may have changed since the last capture.** The display can flip
   between logical sizes mid-session (a 1024×768 reading, then a 1920×1080 capture
   minutes later); coordinates derived from the older image land nowhere while the
   app looks perfectly idle. Re-read `[System.Windows.Forms.Screen]::AllScreens`
   and the capture's real pixel size, and recompute every coordinate from the image
   in hand, never from a previous round.
2. **Another window is eating the clicks.** The capture showing your target proves
   nothing about z-order for input. Enumerate *every* visible window with
   `EnumWindows` + `GetClassName` + `GetWindowRect` — including ones with empty or
   mojibake titles and ones larger than the screen — and minimize the offender by
   class rather than by title:
   ```powershell
   # Windows Terminal / console hosts swallow clicks aimed at the app behind them
   if ($cn.ToString() -eq 'CASCADIA_HOSTING_WINDOW_CLASS') { [MG]::ShowWindow($h, 6) }
   ```
   A console left over from an earlier launch (tab title reads `[ ! ] Action
   Required` after a failed command) is a common occupant; minimize it instead of
   killing processes.
   **Check for duplicates of your own target too**: two windows of the same app can
   sit at the identical rect (a relaunch stacked on the old one), so the screenshot
   shows the live page while every click lands on the dead one underneath/topping
   it. Enumerate titles, close the stale copy by exact title
   (`FindWindow("Chrome_WidgetWin_1", "Home | <site>")` + `PostMessage(h, 0x0010, …)`),
   and re-verify the survivor responds before continuing.
3. **Stuck renderer.** If input still does nothing in a Chromium app window while
   the browser's own chrome responds, relaunch that window fresh instead of
   clicking harder.

> **PowerShell `Add-Type` fails with `TypeNotFound` when the C# class is not minimal.**
> A nested `struct` used by an `out` parameter, or several unrelated DllImports
> crammed into one class, makes the whole block fail to compile while the error
> surfacing is just `<class> was not found`, so the script looks like a logic bug.
> Declare structs at top level (outside the class), keep each `Add-Type` block to the
> handful of imports the script actually calls, and split unrelated helpers into
> separate blocks. Wrap the block in `-TypeDefinition @"…"@` with
> `CharSet=CharSet.Unicode` for `FindWindow` so Chinese titles resolve.

Rules:

**Focus and text entry are a separate problem from clicking.**

- `SetForegroundWindow` is frequently *refused* by Windows' foreground lock: it
  returns without error while the covering window keeps focus, so the next
  `SendKeys "^,"` opens the wrong app's settings. Read back
  `GetForegroundWindow` + `GetWindowText` before sending keystrokes; if the title
  is still the wrong window, minimize the covering window (click its minimize
  box) or click the app's taskbar entry, then re-check.
- Enumerate before guessing: `EnumWindows` + `GetWindowText` + `GetWindowRect`
  gives title, handle and geometry for every visible window in one pass. Chinese
  titles come back mojibake through the WSL console — match an ASCII fragment
  (`ChatGPT`) and keep the handle for `ShowWindow`/foreground calls.
- `SendKeys` cannot type CJK (the IME swallows it). For Chinese into a GUI field:
  `Set-Clipboard -Value "<text>"` inside the same PowerShell script, click the
  input, then `SendKeys "^v"`.
- Never navigate a GUI app by URL or shortcut blindly: a GUI shell may look like
  a browser (same Chromium surface) and `Ctrl+,` / a typed URL then acts on the
  browser instead. Confirm the window identity first.

- **截图给 vision 看过的图会被下采样，坐标必须换算回原图。**
  `vision_analyze` 对大图会缩（1920×1032 → 960×516 并在提示里写「multiply by 2.00」），
  从缩略图上量出的 (676,589) 落到原图就是 (1352,1178)——点在窗口外面，界面上什么都没变，
  看起来像「点击无效 / 应用不响应」，实际是自己点偏了。规矩：点之前先看
  `capture: SAVED <w>x<h>` 的真实像素尺寸，用 **windows 比例**（如水平 0.45、距底 58px）
  而不是缩略图绝对像素；最大化窗口 `GetWindowRect` 会返回 `RECT=0,0`，此时窗口坐标=屏幕坐标。
- **One click per screenshot.** Re-capture between clicks. Chaining two "known"
  coordinates from one stale image closed the app being demonstrated and opened an
  unrelated login window — the foreground changed between the two clicks.
- **The foreground window changes under you.** After any click that opens a
  dialog, link or new window, the next coordinate belongs to a different surface.
  Verify before reusing a coordinate.
- **A non-focused window swallows the click.** Bring the window forward first
  (title bar, taskbar entry, `AppActivate`), confirm with a screenshot, then aim.
- **Click the label, not the widget.** Radio buttons / checkboxes respond
  reliably when the text next to them is the target.
- **Store/MSIX apps have no exe.** `Get-StartApps | ? Name -match '<x>'` yields an
  AUMID; launch via `cmd /c start shell:AppsFolder\<AUMID>`.
- **Native file dialogs: a pasted absolute path navigates, it does not select.**
  Pasting `C:\dir\sub\file.mp3` into the 文件名 field and pressing Enter usually
  jumps *into* `C:\dir\sub`, clears the field, and leaves the file unselected — the
  upload never starts and the dialog just sits there. Do it in two steps: paste the
  absolute path → Enter, then paste `sub\file.mp3` (relative to where you landed)
  → Enter, or select the row with a click and press Enter. Verify by screenshotting
  the web page afterwards; a rejected upload surfaces as a red toast there, not in
  the dialog.
- **A long list that ignores the wheel: zoom the page out instead.** Web-app lists
  often live in their own scroll container, so `mouse_event(0x0800, …)` and
  `{PGDN}` do nothing while the visible rows stay at four or five. `SendKeys "^-"`
  (click the page body first so focus is not on the sidebar) re-flows the layout
  and doubles the rows in one screenshot — much cheaper than dragging an inner
  scrollbar thumb by guessed coordinates.
- **Close the interposed dialog before screenshotting "the app".** A Store/consent
  popup on top of your target makes the capture look like a failure.
- **In a chat UI, every suggestion row is a live submit button.** Clicking blank
  space "to dismiss a menu" can land on a starter task and kick off a real run
  (summarise my inbox, list my files) the user never asked for. Aim at a named
  control or send `{ESC}`; never treat empty-looking area as inert.
- **Taskbar coordinates belong to whatever window owns them.** A stale x/y aimed at
  the taskbar can switch to, or close, the app you were driving and launch
  something unrelated (a chat app's login window, a browser tab). Re-capture after
  any action that changes focus, and confirm the intended window owns the title bar
  before aiming at taskbar or screen-edge coordinates.

### 4.2 往 GUI 应用里代发一条指令（替用户传话）

用户盯着另一个 AI / 应用干活时，典型指令是「你告诉他，让他继续」。把一句话送进
ChatGPT 桌面版这类 UWP 应用的输入框，下面这套是实测能成的最短路径：

```powershell
# ① 强前台：单用 AppActivate / SetForegroundWindow 都可能被前台锁静默拒掉
$fgH  = [Fg]::GetForegroundWindow()
$tidFg = [Fg]::GetWindowThreadProcessId($fgH, [ref]$pidFg)
[Fg]::AttachThreadInput([Fg]::GetCurrentThreadId(), $tidFg, $true) | Out-Null
[Fg]::ShowWindow($target, 9) | Out-Null      # 9 = SW_RESTORE，顺带把窗口还原成正常尺寸
[Fg]::BringWindowToTop($target) | Out-Null
[Fg]::SetForegroundWindow($target) | Out-Null
[Fg]::AttachThreadInput([Fg]::GetCurrentThreadId(), $tidFg, $false) | Out-Null

# ② 坐标每次现算，不要用上一张截图里的绝对像素
[Fg]::GetWindowRect($target, [ref]$r) | Out-Null
$cx = $r.Left + [int](($r.Right - $r.Left) * 0.45)
$cy = $r.Bottom - 58          # 输入框贴底，用「距底边」定位才不随窗口尺寸漂

# ③ 中文不能走环境变量：$env:MSG 经 bash/管道过来是乱码 → 写 UTF-8 文件再读
$msg = [System.IO.File]::ReadAllText('C:\Windows\Temp\msg.txt', [System.Text.Encoding]::UTF8)
Set-Clipboard -Value $msg
[System.Windows.Forms.SendKeys]::SendWait('^v'); Start-Sleep -Milliseconds 900
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
```

- **窗口尺寸会在两次检查之间变**（同一会话里 960×1032 → 870×600），上一轮从截图
  里读出的绝对坐标直接失效。一律 `GetWindowRect` + 相对比例（水平 0.45、距底 58px）
  现算；`SW_RESTORE` 自己就会改尺寸，所以恢复窗口后必须重新取 rect。
- **发完必须用 `PrintWindow` 回读一遍**：界面里出现那句话的气泡才算送到（见 §3）。
  `SendKeys` 不报错不代表输入框收到了字。
- **只做用户明确要你转达的那一句**。他在盯第三方 agent 时，默认状态是「只截图汇报」，
  没说「你告诉他」就不要点按钮、不要代答；这是分工，不是保守。
- 凭据类字段永不代填（见 §4 的规则）。

---

### 4.3 盯守另一个 agent 的 GUI（监护模式：只截图汇报，不代操作）

用户让「你盯着他干活，有情况发我」时的固定做法。适用于桌面版 Codex / ChatGPT、剪映导出、
任何在 GUI 里长跑的第三方 AI。

**架构**：cron 每 10 分钟一轮 → 脚本截图（`PrintWindow`）→ `vision_analyze` 读界面 →
与上一轮状态对比（cron 开 `continuity`）→ **只有实质变化**才用富媒体接口把图推给他。
截图脚本只负责产出路径，判定逻辑放在 prompt 里；`deliver` 用 `local`，消息自己用接口发，
避免同一条通知投递两遍。

**什么算「情况」（才允许推送）**

```
A 任务完成 / 交了新结果
B 报错、弹授权框等人点、额度用完
C 从「干活中」变成「等用户回话」
D 关键数字或方案变更（体积、条数、格式）
```

**反向铁律：同一状态只报一次。** 计时数字跳、进度百分比动、又生成几张图，都不算情况。
按「状态没变就报」写出来的看门狗，一小时能给用户刷 5 条重复提醒，他只会觉得你坏了。

**判活不能只看画面和计时器。** 界面「Working for 12 分 6 秒」连续一小时不动，可能是卡死，
也可能是它在后台跑长命令 / 等模型返回——UI 本来就不刷新。三路交叉验证再下结论：

```powershell
# ① CPU 增量：两次采样，10 秒间隔；持续 ~0.00s = 在等（空转），不是算
$a = Get-Process codex -EA SilentlyContinue | Select Id,CPU; Start-Sleep 10
$b = Get-Process codex -EA SilentlyContinue | Select Id,CPU
# ② 进程在不在（引擎进程名可能是 codex / ChatGPT / node，先 Get-Process 找）
# ③ 出网通不通：代理 200 才算通，SynSent 的连接不能当证据
Invoke-WebRequest 'https://chatgpt.com' -Proxy 'http://127.0.0.1:7890' -TimeoutSec 20 -UseBasicParsing
```

- `CPU 空转 + 进程都在 + 出网 200` = 它在等结果，属于正常，别报「卡死」。
- 真卡死的特征是：弹框没人点、点击无反应、连续两轮完全同一帧，且它自己不会恢复。
- 上一轮判错要**当场更正**并改规矩，不要接着按老规矩继续刷。

**桌面版 Codex（ChatGPT 壳）不写本地会话文件**，`~/.codex/sessions/` 只有命令行 codex 的；
所以对它只有「看画面」这一条路，读不到内部日志。据此设计：能看画面就汇报画面，别承诺「我能看到它的执行细节」。

**代发指令**：用户看完截图说「你告诉他，让他继续」时才动手，走 §4.2；
他没说就只截图，不点按钮、不代答——这是分工，不是保守。

**通知要有第二跳**：他白天上班时 QQ 可能看不着。同一问题报过一次没解决，就换微信催
（`~/projects/codex-wechat/send.js`，详见 `qqbot-media-delivery` §五）；大事件两边都发一次。
只靠单通道写看门狗，等于把「发了」当成「他知道了」。

---

## 5. Accessing Windows Temp Files

```bash
# Discover Windows username
ls <C盘>/Users/

# Temp directory
ls <C盘>/Users/<username>/AppData/Local/Temp/
```

---

## 6. Browser Tab Detection from WSL

When Edge/Chrome is running on Windows, you can detect open tabs and URLs from inside WSL.

### Detect Browser Process

```bash
# Check if Edge is running
<C盘>/Windows/System32/tasklist.exe /FI "IMAGENAME eq msedge.exe" /NH
```

### Get Open Tab URLs (Edge)

The most reliable method is **UI Automation**. This works because the browser exposes its address bar as an accessible edit control:

```bash
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Add-Type -AssemblyName UIAutomationClient; Add-Type -AssemblyName UIAutomationTypes
\$targetPid = 11184  # Edge main process PID
\$root = [System.Windows.Automation.AutomationElement]::RootElement
\$cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, \$targetPid)
\$edgeEl = \$root.FindFirst([System.Windows.Automation.TreeScope]::Subtree, \$cond)
if (\$edgeEl) {
    \$editCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    \$edits = \$edgeEl.FindAll([System.Windows.Automation.TreeScope]::Subtree, \$editCond)
    for (\$i = 0; \$i -lt \$edits.Count; \$i++) {
        try {
            \$vp = \$edits[\$i].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
            \$v = \$vp.Current.Value
            if (\$v.Length -gt 0 -and (\$v -match '^https?://' -or \$v -match '^\d+\.\d+\.\d+\.\d+:\d+')) {
                Write-Host ('URL: ' + \$v)
            }
        } catch {}
    }
}
"
```

### Get Browser Window Titles (Quick Check)

To get visible window titles matching a browser:

```powershell
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Text;
public class W {
    public delegate bool EWP(IntPtr h, int l);
    [DllImport("user32.dll")] public static extern int EnumWindows(EWP e, int l);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern int IsWindowVisible(IntPtr h);
}
'@
# ... (use the EnumWindows callback pattern, filter by title matching 'edge|chrome|firefox')
```

### Limitations
- Chrome tabs may not expose URLs via UI Automation reliably
- Only works for the currently active/focused browser window
- UI Automation requires the target PID — find the main browser process PID first via `Get-Process msedge`
- The `$pid` variable name is **reserved** in PowerShell — use `$targetPid` or another name instead

### See Reference
`references/windows-browser-tabs.md` for the exact working script from this session.

---

## 7. Windows Service Discovery & Investigation

A systematic pattern for discovering and investigating unknown services/applications running on the Windows host from within WSL.

### Phase 1: Detect What's Running

```bash
# List all visible window titles (finds browser tabs, app windows, etc.)
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Text;
public class W {
    public delegate bool EWP(IntPtr h, int l);
    [DllImport(\"user32.dll\")] public static extern int EnumWindows(EWP e, int l);
    [DllImport(\"user32.dll\")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport(\"user32.dll\")] public static extern int IsWindowVisible(IntPtr h);
}
'@
\$results = [System.Collections.ArrayList]@()
\$cb = { \$h = \$args[0];
    if ([W]::IsWindowVisible(\$h)) {
        \$s = New-Object System.Text.StringBuilder 512
        [W]::GetWindowText(\$h, \$s, 512)
        \$t = \$s.ToString().Trim()
        if (\$t.Length -gt 0) { [void]\$results.Add(\$t) }
    }
    return \$true
}
[W]::EnumWindows(\$cb, 0)
\$results | Sort-Object -Unique | ForEach-Object { Write-Output \$_ }
"
```

### Phase 2: Identify Suspicious/Unknown Processes

```bash
# Find processes listening on non-standard ports
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
netstat -ano | Select-String 'LISTENING' | ForEach-Object {
    if (\$_ -match ':(\d+)\s' -and [int]\$matches[1] -gt 10000 -and [int]\$matches[1] -lt 20000) {
        Write-Output \$_
    }
}

# Get process details by PID
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Get-Process -Id 18776 | Select-Object ProcessName, Id, StartTime, CPU, Path
"

# Get detailed command line
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Get-CimInstance Win32_Process -Filter 'ProcessId = 18776' | Select-Object ProcessId, CommandLine
"
```

### Phase 3: Investigate Application Files

```bash
# Find application directories
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Get-ChildItem 'C:\Users\username\.openclaw' -Directory -ErrorAction SilentlyContinue | Select-Object Mode, Name
"

# Read configuration files
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Get-Content 'C:\Users\username\.openclaw\openclaw.json' -Encoding UTF8 | Select-Object -First 50
"

# Find npm packages (search AppData)
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
Get-ChildItem 'C:\Users\username\AppData\Roaming\npm\node_modules' -Directory -Filter '*openclaw*' -ErrorAction SilentlyContinue
"
```

### Phase 4: Probe HTTP Endpoints

If the service is web-based (listening on a port), probe it:

```bash
# Try API endpoints from PowerShell (WSL curl can't reach localhost-bound Windows services)
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "
\$wc = New-Object System.Net.WebClient
\$wc.Headers.Add('User-Agent', 'Mozilla/5.0')
try {
    \$r = \$wc.DownloadString('http://127.0.0.1:18789/')
    Write-Host ('Response: ' + \$r.Substring(0, [Math]::Min(\$r.Length, 500)))
} catch { Write-Host ('FAILED: ' + \$_.Exception.Message) }
"

# Probe common API endpoints
foreach (\$ep in '/health', '/api/status', '/api/version', '/api/config', '/api/info') {
    try {
        \$r = \$wc.DownloadString('http://127.0.0.1:18789' + \$ep)
        Write-Host (\$ep + ': ' + \$r.Substring(0, [Math]::Min(\$r.Length, 300)))
    } catch { Write-Host (\$ep + ': ERROR') }
}

# Analyze JS bundles to find API routes
\$js = \$wc.DownloadString('http://127.0.0.1:18789/assets/index-XXXXX.js')
\$pattern = [regex]'(/api/[a-zA-Z0-9_/-]+)'
\$matches = \$pattern.Matches(\$js)
\$matches | ForEach-Object { Write-Output \$_.Groups[1].Value } | Sort-Object -Unique
```

### Phase 5: Service Context & Integration Detection

Check for common integration directories that reveal what the service connects to:

| Indicator | Look For |
|-----------|----------|
| **QQ Bot** | `qqbot/`, `qqbot/data`, `qqbot/sessions` |
| **WeChat** | `weixin/`, `wechat/`, `openclaw-weixin` |
| **Telegram** | `telegram/`, `tg/` |
| **Discord** | `discord/` |
| **Agent system** | `agents/`, `agent/`, `memory/`, `sessions/` |
| **Plugin system** | `plugins/`, `extensions/`, `skills/` |
| **Backup/Config history** | `.bak`, `.bak.1`, `.last-good` files |

### Phase 6: Communicate with Discovered Services

After discovering a service, the next step is often to **communicate with it programmatically**. Many local AI services expose CLI tools that can be invoked from WSL via PowerShell:

**Pattern for CLI-based communication:**
```powershell
$env:Path = 'C:\Program Files\nodejs;C:\Users\<用户名>\AppData\Roaming\npm;' + $env:Path
$env:OPENCLAW_GATEWAY_PORT = '18789'  # If the service uses a port
$r = node 'C:\Users\<用户名>\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs' agent --message 'hello' --json 2>&1
```

**Checklist for CLI discovery:**
1. Find the npm/global package directory: `C:\Users\<user>\AppData\Roaming\npm\node_modules\<package>\`
2. Find the CLI entry point script (`openclaw.mjs`, `index.js`, `cli.js`, etc.)
3. Check for a `.cmd` wrapper in the npm bin directory
4. Run `--help` to discover available commands
5. Look for `agent`, `message`, `send`, `chat` subcommands for AI-to-AI communication

**Key insight: WSL localhost limitation**
Windows services bound to `127.0.0.1` are NOT accessible from WSL curl. Use PowerShell on the Windows side (`<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`) to make HTTP requests to localhost-bound services, OR use the service's CLI tool directly (CLIs often connect via WebSocket/pipe internally).

### Key Insight: WSL Localhost Limitation

Windows services bound to `127.0.0.1` (loopback-only) are **NOT accessible from WSL curl** — WSL2 uses a separate network stack. Always use PowerShell on the Windows side (`<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`) to make HTTP requests to localhost-bound services.

The `health` endpoint often works when other API routes don't (even for SPAs). Read the JS bundle to discover real API routes if the SPA doesn't expose them via OpenAPI.

---

---

## 8. Locating Windows Applications (Non-Standard Paths)

When a Windows app isn't in its expected install directory (e.g., WeChat installed at `C:\Program Files\Tencent\Weixin\Weixin.exe` instead of `C:\Program Files (x86)\Tencent\WeChat\WeChat.exe`), search via Start Menu shortcuts:

### Step 1: Search Start Menu for the App

```powershell
# Search by app name (Chinese or English)
Get-ChildItem 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs' -Recurse -Filter '*微信*' -ErrorAction SilentlyContinue | Select-Object FullName, Target
# Or search by English name
Get-ChildItem 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs' -Recurse -Filter '*WeChat*' -ErrorAction SilentlyContinue | Select-Object FullName, Target
```

### Step 2: Resolve the Shortcut Target

```powershell
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut('C:\ProgramData\Microsoft\Windows\Start Menu\Programs\微信\微信.lnk')
Write-Host $lnk.TargetPath
# Output: C:\Program Files\Tencent\Weixin\Weixin.exe
```

### Step 3: Launch the Application

```powershell
# Launch from WSL via PowerShell
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "Start-Process 'C:\Program Files\Tencent\Weixin\Weixin.exe'"

# Verify it's running
<C盘>/Windows/System32/tasklist.exe /FI "IMAGENAME eq Weixin.exe" /NH
```

### ⚠️ Common Non-Standard Install Names

| App | Expected Path | Actual Install Path |
|-----|---------------|-------------------|
| **WeChat** | `...\Tencent\WeChat\WeChat.exe` | `...\Tencent\Weixin\Weixin.exe` (new version) |
| **QQ (NT)** | `...\Tencent\QQ\Bin\QQScLauncher.exe` (legacy QQ) | `C:\Program Files\Tencent\QQNT\QQ.exe` (new NT version, verified 2026-07) |

Always verify the file exists before trying to launch: `ls -la "<C盘>/Program Files/Tencent/Weixin/Weixin.exe"`

### Avoiding Full-Drive Recursive Searches

`Get-ChildItem -Path 'C:\' -Filter '*.exe' -Recurse` will **time out** on large drives. Instead, search specific locations in order:

1. **Start Menu shortcuts** (fastest) — search `C:\ProgramData\Microsoft\Windows\Start Menu\Programs`
2. **Common install dirs** — `Program Files`, `Program Files (x86)`, `%LOCALAPPDATA%`
3. **Desktop shortcuts** — `C:\Users\<user>\Desktop\`
4. **User AppData** — `C:\Users\<user>\AppData\Local\`, `C:\Users\<user>\AppData\Roaming\`

### winget-installed apps: exe is under `%LOCALAPPDATA%\<App>\Apps\`, and the registry is empty

`winget install --id <Publisher.App>` can report `Successfully installed` while the app leaves **no Uninstall registry entry** and no `Program Files` folder — its updater-style installer drops a per-user tree instead. Searching the registry then reports nothing and looks like a failed install.

| App | Real exe |
|---|---|
| 剪映专业版 (`ByteDance.JianyingPro`) | `%LOCALAPPDATA%\JianyingPro\Apps\JianyingPro.exe` (重定向到 `Apps\<version>\`) |

Procedure that actually works:

```powershell
winget install --id ByteDance.JianyingPro -e --accept-package-agreements --accept-source-agreements
# 1) winget 自报已装（不信它，只当作线索）
winget list --id ByteDance.JianyingPro
# 2) 直接在 LOCALAPPDATA 下找 exe，不要翻注册表、不要全盘搜
Get-ChildItem $env:LOCALAPPDATA -Recurse -Depth 4 -Filter "JianyingPro.exe" -File | Select-Object -First 3
# 3) 从 launcher 建快捷方式（桌面 + 开始菜单），名字用码点拼
```

Notes:
- 剪映这类 Electron 壳启动后 `Get-Process` 会看到 **10 个以上同名进程**，这是正常的（主进程 + 渲染 + tray），不是重复安装。
- 窗口不一定在前台：`Get-Process JianyingPro | ? MainWindowHandle -ne 0` 拿到 handle，`ShowWindow(h,9)` 还原 + `SetForegroundWindow(h)` 再截图，否则截到的是空桌面。
- 剪映自带 `jianying-agent-cli.exe`（在 `Apps\<version>\` 里），意味着可以用命令行批量处理，不必全靠点界面。
- **「现在开通，低至 X 元/天」是广告位，对已登录的 SVIP 也照常显示，绝不能拿它判断登录状态。** 判断登录看 `菜单 → 账号`：子菜单里出现「永久注销账号」= 已登录，出现「登录」= 未登录。判断会员点那条广告，弹出的「订阅服务」面板顶部才写真实状态（昵称 + `SVIP 2026.11.25 到期` + 云空间/积分）。
- 未登录时导出可能带水印/限分辨率；用户说「我扫了」时先按上面的方法查证再回话，别照着广告位断言他没登录。
- 剪映的编辑页没有「登录」按钮，登录入口只在 `菜单 → 账号`；顺带一条：Electron 应用的 `AutomationElement` 树有 100+ 节点但 Name 全为空，UI Automation 找不到按钮——直接读截图取坐标点击（§4.1）。

### No desktop build? Wrap the web app in its own window

Before installing some third-party "desktop version" of a web service, check
whether an official one exists. When it does not, a Chrome app window is the
closest thing to a native client and costs one shortcut:

```powershell
$ws = New-Object -ComObject WScript.Shell
$chrome = "C:\Users\<user>\AppData\Local\Google\Chrome\Application\chrome.exe"
foreach ($t in @((Join-Path ([Environment]::GetFolderPath('Desktop')) 'App.lnk'),
                 (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\App.lnk'))) {
  $s = $ws.CreateShortcut($t)
  $s.TargetPath  = $chrome
  $s.Arguments   = '--app=https://site.example --proxy-server=http://127.0.0.1:7890 --window-size=1280,860'
  $s.IconLocation = "$chrome,0"
  $s.Save()
}
```

- `--app=` drops the address bar and tab strip, so the window reads as an app.
- `--proxy-server=` pins the proxy to that window only — do not rely on the system
  proxy toggle, which may be off because another task needed it off.
- Chrome installs per-user; find the real path by resolving the existing
  `Google Chrome.lnk` (`$ws.CreateShortcut($lnk).TargetPath`) instead of guessing
  `Program Files`.
- Verify by launching the shortcut and screenshotting: a working window shows the
  site's own UI with no browser chrome. Sign in by clicking the account row the
  browser already has a session for — never type credentials.

---

## 9. OpenClaw (真维斯) QQ Bot 配置

OpenClaw 运行在 Windows 上，支持通过 QQ 开放平台接入 QQ Bot。详细配置步骤、凭证获取方式、平台限制及从 WSL 配置的完整流程见：

📍 **参考文件：** `references/openclaw-qqbot-config.md`

### 核心要点速览

- 配置文件路径：`%USERPROFILE%\.openclaw\openclaw.json`
- 渠道配置字段名必须是 `qqbot`（不是 `qq`）
- 需要先在 [QQ 开放平台](https://q.qq.com/) 注册 Bot 获取 AppID 和 Client Secret
- QQ 平台限制：不能发 URL、不支持 Markdown、主动消息有窗口期
- 三 AI 协作最佳实践：小爱（Hermes）在 QQ 上接收指令 → delegate 给真维斯执行 → 汇总结果返回

---

## 9.5 关屏 / 显示器控制：这台机器走不通（2026-11-08 实测）

**这台 M920q 在 Windows 眼里没有物理显示器。** 证据：

```
Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBasicDisplayParams
→ NotImplemented (0x8004100c)，返回 0 个显示器
```

后果与结论：

```
❌ SendMessage(0xffff, 0x0112, 0xF170, 2)   返回 1，但屏幕不黑
❌ nircmd monitor off                        同一个 Win32 消息，同样无效
❌ xset dpms force off                        WSL 里没有 X11，同样无效
✅ 只能物理按显示器电源键，或系统电源策略设自动关屏
```

分辨率长期卡 1024×768 是同一个根因；要改分辨率先解决显示驱动，不要指望命令。

### 物理世界操作的验收：看结果不看返回码

任何「碰到物理世界」的命令（关屏、调音量、鼠标点击、喇叭发声），**返回码成功不等于事情发生了**。

- 命令侧只报：执行完了没、stdout 是什么
- **结果侧必须从外部验**：截图量平均亮度（`ImageStat`）、抽帧看画面、读产物文件大小
- 宁可报「看不到物理屏幕，需用户确认」，也不要报「成功了」

实测：`SendMessage` 返回 1 只代表消息发出去了，屏幕平均亮度仍 70.4、最大 255（亮着）。

## 10. OpenClaw 故障诊断

OpenClaw 本地部署后"崩溃"或无法启动时，系统性诊断流程。

### 快速检查清单

```bash
# 1. 确认进程是否存在
<C盘>/Windows/System32/tasklist.exe /FI "IMAGENAME eq node.exe" /NH

# 2. 确认端口监听
<C盘>/Windows/System32/netstat.exe -ano | findstr :18789

# 3. 尝试运行获取版本/错误信息（必须使用Windows路径格式）
<C盘>/Program\ Files/nodejs/node.exe "C:\Users\<user>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" --version
```

### 常见根因：Node.js 版本不兼容

OpenClaw 对 Node.js 版本有严格要求。如果运行时报错：

```
openclaw requires Node >=22.22.3 <23, >=24.15.0 <25, or >=25.9.0.
Detected: node 25.8.1
```

意味着当前 Node.js 版本落在不支持的间隙中。修复方案：
- **升级** Node.js 到 v25.9.0+ 或 **降级** 到 v24.15.0+ (LTS)

### 诊断路径与日志位置

| 位置 | 说明 |
|------|------|
| `~/.openclaw/logs/config-health.json` | 配置健康状态 |
| `~/.openclaw/logs/stability/*.json` | 崩溃快照（含进程信息、错误堆栈）|
| `~/.openclaw/logs/gateway-restart.log` | 重启历史 |
| `~/.openclaw/gateway.cmd` | 旧版启动脚本 |

📍 **详细诊断案例：** `references/openclaw-troubleshooting.md`

### ⚠️ 从 WSL 运行 Windows node.exe 的路径格式

**WSL 的 `<C盘>/...` 路径不能直接传给 Windows 的 node.exe。**

```bash
# ❌ 失败 — Windows node 会解析为 UNC 路径并报模块不存在
<C盘>/Program\ Files/nodejs/node.exe <C盘>/Users/.../index.js

# ✅ 正确 — 使用 Windows 原生路径格式（即使在 WSL 中调用）
<C盘>/Program\ Files/nodejs/node.exe "C:\Users\<user>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" --version
```


---

## 11. File Delivery to Remote Users (When Local Access Unavailable)

When the user is not at the machine and the QQ Bot cannot send file attachments proactively, upload the file to a web-accessible service and share the URL.

### Content-Type Problem: paste.rs

`paste.rs` returns raw content — browsers display HTML source code instead of rendering it. It does NOT set `Content-Type: text/html` properly for browser rendering.

### Solution: litter.catbox.moe

Upload to `litterbox.catbox.moe` — returns proper `Content-Type: text/html` with correct content-length and `.html` extension:

```bash
# Upload to litter.catbox.moe (temp storage, 72h default)
curl -s --max-time 20 \
  -F "reqtype=fileupload" \
  -F "time=72h" \
  -F "fileToUpload=@/path/to/file.html" \
  "https://litterbox.catbox.moe/resources/internals/api.php"

# Returns: https://litter.catbox.moe/<hash>.html
```

### Verification Pattern

Always verify both content-type AND content-length after upload:

```bash
curl -sI --max-time 10 "https://litter.catbox.moe/xxxx.html" | head -10
```

Check for:
- `content-type: text/html` — browser will render
- `content-length` matches original file size
- URL ends in `.html` — browser treats it correctly

### Alternative: temp.sh (but check content-type)

```bash
# Upload
curl -s --max-time 15 -F "file=@/path/to/file.html" "https://temp.sh/upload"

# Check — temp.sh returns wrapper pages (3084 bytes) not the actual file
# Only use when the actual file needs to be downloaded, not previewed
```

### Pitfall: GitHub Gist Unauthenticated Upload Fails

```bash
# This WILL fail with 401 — requires authentication
curl -X POST -H "Content-Type: application/json" -d @payload.json "https://api.github.com/gists"
# Response: {"message": "Requires authentication", "status": "401"}
```

### Pitfall: paste.rs Renders Raw Source Code

`paste.rs` is a plain-text pastebin — it strips or doesn't set proper Content-Type for HTML. Browsers show the HTML source code, not the rendered page. **Always use litter.catbox.moe for HTML files that need to render as web pages.**

---

## 12. Writing Batch Files That Launch WSL Commands

### ⚠️ Critical Rule: Shell Script First, Bat Calls Script

**The most robust approach: create a WSL shell script, then have the .bat call it with `wsl bash ~/script.sh`.**

This eliminates ALL CMD escaping issues — no `|`, `&&`, `&`, `>`, `<`, or `"` can be misparsed because the bat contains no special characters:

```bat
@echo off
chcp 65001 >nul
wsl bash ~/my-launcher.sh
pause
```

The shell script handles all the logic (cd, source venv, run program):

```bash
#!/bin/bash
cd ~/project-dir || { echo "[错误] 目录不存在"; exit 1; }
source venv/bin/activate || { echo "[错误] 虚拟环境激活失败"; exit 1; }
exec python -m my_module "$@"
```

This is the **preferred pattern** for any bat file that launches a WSL-based service or CLI. It works because:
- CMD only sees `wsl bash ~/script.sh` — no special characters to intercept
- bash receives the script path directly, no quoting confusion
- The shell script can include error handling, logging, and multi-step setup
- The script is editable within WSL without touching the bat file

### The Pipe-Inside-Quotes Trap (Critical)

When writing a `.bat` file that passes a compound command to `wsl.exe bash -c "..."`, **Windows CMD interprets `|`, `&`, `&&`, `||`, `>`, `<` as its own operators even inside double-quoted strings.** This is a well-known CMD parsing behavior that differs from Unix shells.

```bat
@echo off
REM WRONG — CMD intercepts the pipe inside quotes
wsl.exe bash -ic "cd ~/repo && source venv/bin/activate && python script.py 2>&1 | tee -a /tmp/log.txt"
```

**What CMD actually does with the line above:**
CMD sees `|` inside the double quotes and splits into two commands:
- **Command 1:** `wsl.exe bash -ic "cd ~/repo && ... && python script.py 2>&1 "`
- **Pipe** →
- **Command 2:** `tee -a /tmp/log.txt`

Windows has no `tee` command → `'tee' 不是内部或外部命令, 也不是可运行的程序`

#### The `&&` Trap: Also Intercepted by CMD

⚠️ **`&&` inside double-quoted strings IS also treated as a CMD command separator in many Windows environments.** This is the same mechanism as the `|` pipe problem. Even though `&&` appears to be "inside quotes" from a human perspective, CMD's parser recognizes `&&` as an unconditional command separator before fully resolving quote boundaries in certain configurations.

This means:

```bat
REM WRONG — CMD may split on && inside the string too
wsl.exe bash -ic "cd ~/.hermes/hermes-agent && source venv/bin/activate && python -m module"
```

CMD can interpret this as three separate commands:
- Command 1: `wsl.exe bash -ic "cd ~/.hermes/hermes-agent` (quotes unbalanced!)
- Command 2: `source venv/bin/activate` (CMD tries to run `source` as Windows command)
- Command 3: `python -m module"` (stray quote)

**Fix:** Use the shell-script-first approach above, or if inline is unavoidable, use only `;` (semicolons work in bash for sequential execution) and avoid `&&`, `|`, `>`, `<` altogether.

### ⚠️ Never expand `$PATH` in the command the bat passes to WSL

Interop injects the **Windows** PATH into the WSL process, and it contains spaces
(`C:\Program Files\WSL\...`). Any unquoted expansion inside the launched command
word-splits and the shell dies before the real program starts:

```bat
REM WRONG — bash receives a split PATH
export PATH=$HOME/.local/bin:$PATH
REM → bash: export: `Files/WSL/:<C盘>/Program': not a valid identifier
REM   env: 'node': No such file or directory
```

**Fix:** set PATH **inside a wrapper script** using absolute paths only, and let
the bat call the wrapper with no expansions at all:

```bash
#!/usr/bin/env bash
# ~/.local/bin/<name> — absolute PATH, no inheritance from Windows
export PATH="/home/<user>/.local/bin:/usr/bin:/bin"
export SOME_KEY="$(cat /home/<user>/.hermes/<keyfile>)"
exec /home/<user>/.local/bin/<program> "$@"
```

```bat
wsl.exe -d <distro> -- bash -lc "<name>"
```

Quoting the export (`export PATH="...:$PATH"`) avoids the split but still inherits
~40 Windows paths; the wrapper is strictly better and also lets you bake in the
env vars so the user never exports anything by hand.

### ⚠️ Chinese in a .bat: chcp 65001 is not enough — save as GBK

`chcp 65001` + a UTF-8-saved bat is the documented default here, but a bat whose
`title`/`echo` lines contain Chinese can still be misparsed mid-word — symptom is
nonsense like `'le' 不是内部或外部命令` (i.e. `title` split at byte 3) followed by
several more bogus command errors, and the real program never launches.

**When that happens, stop fighting it: re-save the bat as ANSI/GBK (cp936) and
drop `chcp`.** cmd.exe's native code page then reads the bytes correctly.

```python
open(bat_path, "w", encoding="gbk", errors="replace").write(content)
```

If the bat only needs an error message or two, pure ASCII English is the lowest-risk
option and reads fine on Chinese Windows.

### Launching a .bat from WSL: use PowerShell `Start-Process`

`cmd.exe /c start "" X.bat` invoked from WSL inherits the UNC cwd and prints
`UNC 路径不支持` / `\wsl.localhost\... 因为当前目录是 UNC 路径` — the bat may still run
but you lose control of the working directory. Reliable form:

```bash
PS=<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
$PS -NoProfile -Command "Start-Process -FilePath 'C:\path\to\X.bat' -WorkingDirectory 'C:\path\to'"
```

### Verify a GUI launch with a screenshot, never assume

After launching an interactive app, wait 10–15s, capture the screen (§3), and
`vision_analyze` it before telling the user it is ready. The screenshot also
surfaces things you cannot see from WSL — an error dialog, a corrupted batch
window, or icons the user already has on their desktop that change your advice.

### Diagnosis Checklist (WSL-Launching .bat Fails)

| Symptom | Likely Cause |
|---------|-------------|
| Window flashes and closes immediately | CMD split on `|`, `&&`, or `&` — second command not found |
| `'tee' is not recognized` | Pipe intercepted by CMD inside quotes |
| `'source' is not recognized` | `&&` split the command chain — CMD tries to run `source` as Windows command |
| `'cd' is not recognized` | Same — CMD split before bash ever executed |
| Window opens, WSL starts, then nothing | bash interactive mode `-i` loads `.bashrc` with conda/nvm that block |
| `python3` not found | Some WSL distros lack `python3` — use `python` (venv has both) |
| Error message appears and window closes before you can read it | Missing `pause` at end of bat, or error happens in WSL bash silently |
| `~` not expanding to home dir | Add a diagnostic script that writes to Windows desktop to test the pipeline |
| All symptoms above persist with shell-script approach | Try absolute paths: `C:\Windows\System32\wsl.exe -e /bin/bash /absolute/path/script.sh` |

### Fix: Use Shell Script + `wsl bash ~/script.sh`

**Best — WSL shell script with absolute path (most robust):**
```bat
C:\Windows\System32\wsl.exe -e /bin/bash /home/clown_zy/hermes-gateway.sh
```

Absolute paths (`/home/user/` not `~/`) and the `-e` flag eliminate all shell expansion ambiguity. Use this variant when the basic form fails silently.

**Best — WSL shell script (recommended):**
```bat
wsl bash ~/hermes-gateway.sh
```

Where `~/hermes-gateway.sh` contains:
```bash
#!/bin/bash
cd ~/.hermes/hermes-agent || { echo "[错误] 路径不存在"; exit 1; }
source venv/bin/activate || { echo "[错误] 虚拟环境激活失败"; exit 1; }
exec python -m hermes_cli.main gateway run --replace
```

**Good — Inline without pipes (no `|`, no `&&` needed if using `;`):**
```bat
wsl.exe bash -c "cd ~/repo && source venv/bin/activate && python script.py >> /tmp/log.txt 2>&1"
```
Note: `&&` here still carries risk — test on target Windows version.

**Adequate — Escape pipe with `^` (fragile):**
```bat
wsl.exe bash -ic "cd ~/repo && source venv/bin/activate && python script.py 2>&1 ^| tee -a /tmp/log.txt"
```
The `^|` prevents CMD from treating `|` as a pipe. The caret is consumed by CMD, bash receives the literal `|`.

### Other .bat Best Practices

- **Use `python` not `python3`** — the venv's `bin/` has both symlinks, but the system WSL may not have `python3` as an independent command
- **Always use `chcp 65001`** at the top of `.bat` files for UTF-8 Chinese character display (especially important on Chinese Windows)
- **Keep bat files simple** — ideally just `wsl bash ~/script.sh` with Chinese echo/header and pause
- **Add `pause >nul` at the end** so the window doesn't close immediately on error — the user can see what went wrong
- **Check if the program writes its own logs** before adding `tee` — Hermes gateway auto-logs to `~/.hermes/logs/gateway.log`. Extra piping can introduce CMD parsing bugs for zero benefit.
- **For checking if a bat ran successfully** from this WSL session, run the bat from CMD with `pause` at the end: `wsl cmd.exe /c "D:\\test.bat"` and look for the pause prompt

---

## 13. Hermes Agent Data Backup (absorbed from hermes-backup)

Automated, daily backup of Hermes Agent's persistent data: sessions, config, memory, and skills. Uses the WSL↔Windows cross-platform patterns from the sections above.

### When to Use

User asks to "back up my data" / "back up memory" / "protect against data loss" / set up recurring backups.

### Backup Script Template

```bash
#!/bin/bash
# ============================================================
# Hermes Agent Auto-Backup Script
# Backs up: memory, sessions, config, .env, skills
# Retention: 30 days
# ============================================================
set -e
BACKUP_DIR="/path/to/backup/dir"
HERMES_HOME="$HOME/.hermes"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hermes_backup_$DATE.tar.gz"

# 1. Copy sessions
[ -d "$HERMES_HOME/sessions" ] && { mkdir -p "$BACKUP_DIR/sessions"; cp -r "$HERMES_HOME/sessions/"* "$BACKUP_DIR/sessions/" 2>/dev/null || true; }
# 2. Copy config
[ -f "$HERMES_HOME/config.yaml" ] && cp "$HERMES_HOME/config.yaml" "$BACKUP_DIR/config_$DATE.yaml"
# 3. Copy .env (sensitive — handle with care)
[ -f "$HERMES_HOME/.env" ] && cp "$HERMES_HOME/.env" "$BACKUP_DIR/env_$DATE.bak"
# 4. Copy skills
[ -d "$HERMES_HOME/skills" ] && { mkdir -p "$BACKUP_DIR/skills"; cp -r "$HERMES_HOME/skills/"* "$BACKUP_DIR/skills/" 2>/dev/null || true; }
# 5. Package tarball
tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" sessions config_$DATE.yaml env_$DATE.bak skills 2>/dev/null && \
  rm -rf "$BACKUP_DIR/sessions" "$BACKUP_DIR/config_$DATE.yaml" "$BACKUP_DIR/env_$DATE.bak" "$BACKUP_DIR/skills"
# 6. Rotate (30 days)
find "$BACKUP_DIR" -name "hermes_backup_*.tar.gz" -mtime +30 -delete 2>/dev/null || true
echo "[$DATE] Backup: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))" >> "$BACKUP_DIR/backup_log.txt"
```

### Multi-Agent Backup (<项目目录>)

| AI | Backup Source | Correct Path |
|:---|:--------------|:-------------|
| 小爱 | WSL | `~/.hermes/memories/` (NOT `~/.hermes/memory/`) |
| 真维斯 | Windows `%USERPROFILE%` | `.openclaw\\memory\\` (NOT `agents\\main\\memory\\`) |
| 阿酷 | Windows `%USERPROFILE%` | `.claude\\history.jsonl` + settings + stats |

**WSL-side (小爱):**
```bash
cp -r ~/.hermes/memories/* <项目目录>/记忆存储/小爱/
cp -r ~/.hermes/sessions/* <项目目录>/备份/日备份/$(date +%Y%m%d)/hermes-sessions/
```

**Windows-side (真维斯 + 阿酷 via PowerShell):**
```powershell
# Uses PowerShell from WSL as described in §2
Copy-Item "$env:USERPROFILE\.openclaw\memory\*" "D:\<项目目录>\记忆存储\真维斯\" -Recurse -Force
Copy-Item "$env:USERPROFILE\.claude\history.jsonl" "D:\<项目目录>\记忆存储\阿酷\" -Force
```

### USB Export/Import

See `references/usb-backup-audit.md` for export checklist.

### Setup Steps

1. `mkdir -p "<项目目录>"` (translate Windows D: to WSL `<D盘>/`)
2. Save the bash script, `chmod +x`
3. Test: `bash /path/to/backup.sh`
4. Schedule: `crontab -e` → `0 3 * * * /path/to/backup.sh`

### Pitfalls (Backup)

1. **WSL path translation**: `C:\...` → `<C盘>/...`, `D:\...` → `<D盘>/...`
2. **.env sensitivity**: Backup tarballs are unencrypted. Store on encrypted volume.
3. **Session lock contention**: Schedule backups for low-traffic hours (3 AM).
4. **Test restore**: `tar -tzf hermes_backup_*.tar.gz | head -20`
5. **Duplicate cron jobs**: Check for existing backup jobs before creating new ones.

### Reference Documents (moved to this skill)

- `references/three-ai-memory-paths.md` — Detailed memory locations
- `references/usb-backup-audit.md` — USB export audit checklist

---

## Pitfalls

| Issue | Symptom | Fix |
|---|---|---|
| **DPI scaling** | Screenshot only captures 1/4 of screen | Use `GetDeviceCaps(DESKTOPHORZRES)` for physical resolution |
| **Permission denied** | Can't write to `<C盘>/` | Write to WSL `/tmp/` or use PowerShell to write from Windows side |
| **UNC path in CMD** | `CMD.EXE` says "UNC path not supported" | CMD can't start from a UNC path; prepend drive letter: `cmd.exe /c "D: && D:\script.bat"` — the warning is harmless, the script still runs |
| **No interactive desktop** | GDI+ CopyFromScreen fails | PowerShell must create a hidden Form first to establish a message pump |
| **PowerShell inline quotes** | Complex scripts break with `;` chaining | Use a script file (.ps1) or careful escaping |
| **Batch file CRLF** | `.bat` file parsed incorrectly; `echo` not recognized | WSL write_file produces LF endings; fix with `sed -i 's/$/\\r/'` |
| **UNC path in CMD** | `cmd.exe` says "当前目录是 UNC 路径" or fails to find paths with spaces | `cmd.exe` cannot start from WSL's `\\wsl.localhost\...` UNC path. **Fix:** `cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "..."` — the UNC warning is harmless, command still runs. For `start` in batch files, `start "" "program path"` (double double-quotes for the title) |
| **Windows `start` in batch from WSL** | `start "Title" cmd /c "..."` fails — can't find the title file | Use `start /B "" "C:\Program Path\node.exe" args...` — empty title, `/B` same window |
| **SetForegroundWindow silently ignored** | Keystroke lands in the covering app (settings dialog of something unrelated) | Verify `GetForegroundWindow` title before `SendKeys`; minimize the covering window or click the taskbar entry first |
| **SendKeys drops Chinese** | GUI field stays empty after typing CJK | `Set-Clipboard -Value` then `SendKeys "^v"` |
| **QR code screenshot login** | QQ rejects QR codes scanned from photos (security feature) | User must open the site on their own device; screenshot-based QR sharing won't work |
| **Pipe `|` inside `"..."` in .bat** | `wsl bash -c "... | tee ..."` fails — `'tee' is not recognized` | CMD parses `|` as its own pipe even inside `"..."`. Remove pipe from the string, or escape with `^|` |
| **WSL path to Windows executable** | `node.exe <C盘>/.../script.js` fails with MODULE_NOT_FOUND | Windows 可执行文件接收的参数路径必须使用 Windows 原生格式 `C:\Users\...`，不能用 WSL 的 `<C盘>/...` |

---

## 14. WSL 资源配置与「从内部重启 WSL」

给 WSL 定内存/swap 上限，以及重启整个 WSL 虚拟机而不断送当前回复。完整模板、命令与验证步骤见：

📍 `references/wsl-resource-and-restart.md`

四条必须先记住的规则：

1. **先量宿主物理内存再定上限**——`powershell.exe -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB"`。WSL2 默认吃 50%，上限超过宿主物理内存会把 Windows 拖进换页。
2. **swap 是和内存同量级的一等配置**，默认 1G 是长驻服务 OOM 的主因；8G 宿主机器给 4G 内存 + 4G swap。
3. **不要设 `vmIdleTimeout`**——VM 空闲自动关闭会连带杀掉网关和定时任务。
4. **从 WSL 内部重启 WSL 要用 schtasks 延迟触发**，让 Windows 任务计划程序在虚拟机外执行 `wsl --shutdown`；直接调用会杀掉自己那棵进程树，关机动作可能做不完整。重启后 VM 不会自己醒，必须提示用户开一次 WSL 终端（依赖 `/etc/wsl.conf` 的 `systemd=true` + `Linger=yes` 才会自动拉起 user service）。

---

## 15. WSL 接管 Windows 上的代理（Clash）

### 🔴 第一原则：GUI 上的开关 = 配置文件里的一个字段，永远先想改配置/调 API

**不要把「GUI 开关」当成「必须人手动点」。** 桌面软件的勾选项几乎都是配置文件的一个布尔字段，改文件或打它的 RESTful API 效果与点击完全等价，而且不需要人守着。说「这一步得你点」之前，先按下面的顺序找替代：

```
① 配置文件字段（最稳，改完下次启动生效）
② 软件的 RESTful / HTTP API（改完立刻生效，不用重启）
③ 命令行参数 / 环境变量
④ 最后才是模拟鼠标点击（要截图找坐标，慢且易错）
```

**同理，软件没在跑时不要等着用户去开** —— 用 `Start-Process` 自己启动它，然后验证端口。本机上的软件属于可操作范围，不是需要用户代劳的外部系统。

### 完整接管流程（照做即可）

**Step 1 — 定位配置文件与关键字段**

```bash
CFG="<C盘>/Users/<user>/.config/clash/config.yaml"
grep -nE "^(allow-lan|port|socks-port|mixed-port|external-controller|secret):" "$CFG"
```

关键字段含义：

| 字段 | 含义 | 常见陷阱 |
|:---|:---|:---|
| `allow-lan` | 是否允许局域网访问 | 默认 `false`，WSL 因此连不上，**必须改 `true`** |
| `mixed-port` | HTTP+SOCKS 混合端口 | 常见 7890 / 7897，**要实测不要假设** |
| `external-controller` | RESTful API 监听地址 | **不一定是 9090**，桌面版常随机分配（如 `127.0.0.1:32975`），必须从配置里读 |
| `secret` | API 鉴权令牌 | 有它就要求 `Authorization: Bearer <secret>` |

**Step 2 — 改 `allow-lan`（用 Python，不用 sed）**

```python
import shutil, time
CFG = "<C盘>/Users/<user>/.config/clash/config.yaml"
shutil.copy2(CFG, CFG + f".bak.{time.strftime('%Y%m%d_%H%M%S')}")
with open(CFG, encoding="utf-8") as f:
    t = f.read()
with open(CFG, "w", encoding="utf-8", newline="\n") as f:
    f.write(t.replace("allow-lan: false", "allow-lan: true"))
```

WSL 里改 Windows 上的 YAML 用 Python 直读 `<C盘>/` 最稳（见 §1：避免 PowerShell 编码管道）。改完必须回读确认，不要只看写出成功。

**Step 3 — 软件没跑就自己启动**

```bash
PS=<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
$PS -NoProfile -Command "Start-Process -FilePath 'C:\Program Files\Clash for Windows\Clash for Windows.exe' -WorkingDirectory 'C:\Program Files\Clash for Windows'"
sleep 12   # Electron 应用要 10s 左右才把代理端口拉起来
```

**Step 4 — 从 WSL 探端口（用 Windows 网关 IP，不是 127.0.0.1）**

WSL2 和 Windows 是两个网络栈：Windows 上绑 `127.0.0.1` 的服务，WSL 里访问不到。要用默认网关 IP：

```bash
WIN_IP=$(ip route | awk '/^default/{print $3; exit}')   # 常见 172.x.x.1
for p in 7890 7897 7891 10809 1080; do
  timeout 2 bash -c "cat < /dev/null > /dev/tcp/$WIN_IP/$p" 2>/dev/null && echo "✅ $WIN_IP:$p"
done
```

**Step 5 — 用 `curl -x` 显式走代理，不要全局 export**

```bash
PROXY="http://$WIN_IP:7890"
curl -s -x "$PROXY" -o /dev/null -w "%{http_code} %{time_total}s\n" https://www.google.com
curl -s -x "$PROXY" --max-time 15 https://api.ipify.org   # 确认出口 IP 变了
```

⚠️ **`export http_proxy=...` 会污染所有子进程**，包括浏览器自动化的 daemon（表现为 `Page.navigate timed out`，看起来像浏览器坏了，其实是它拿走了代理后卡住）。**默认用 `-x` 逐条显式传代理**；确需全局时，写进独立文件 `~/.proxy_env` 并在 `.bashrc` 里留成注释行，按需 `source`，用完 `unset`。

**Step 6 — API 强制生效（双保险，可选）**

配置文件改完要重启才生效；API 是立刻生效，两者可叠加：

```bash
SECRET=$(grep '^secret:' "$CFG" | awk '{print $2}' | tr -d '\r')
CTRL=$(grep '^external-controller:' "$CFG" | awk '{print $2}' | tr -d '\r')
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH "http://$CTRL/configs" \
  -H "Authorization: Bearer $SECRET" -H "Content-Type: application/json" \
  -d '{"allow-lan":true}'
# 204 / 200 = 成功
```

注意 `$CTRL` 绑的是 Windows 的 `127.0.0.1`，从 WSL 里 curl 不通是正常的 —— 这一步用 PowerShell 在 Windows 侧执行才有意义。

### 通了之后：过反爬站的请求头

有代理之后，境外站返回 403 多半不是网络问题，是 UA/压缩协商被识别。**带完整浏览器头 + `--compressed`** 就能过：

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
curl -s -x "$PROXY" --compressed \
  -H "User-Agent: $UA" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "Accept-Encoding: gzip, deflate, br" \
  -o /tmp/page.html -w "%{http_code} %{size_download}B\n" \
  "https://scholar.google.com/scholar?q=<query>&hl=en"
```

缺 `--compressed` 时 Google 系站点容易返回 403；缺 `Accept-Language` 会拿到非预期语言版本。

### 常见状态码判读（别把非 200 一律当失败）

| 状态 | 真实含义 | 处理 |
|:---|:---|:---|
| `200` | 通 | — |
| `302`（google.com 等） | 同意页/地区跳转 | 加 `-L` 跟随，通常即 200 |
| `403` + Cloudflare 站点 | 该出口节点被风控 | 换节点，或走该内容的镜像站（如期刊文章的 PMC 副本） |
| `403` + Google Scholar 用 curl | 缺浏览器头/压缩协商 | 按上一节补头 + `--compressed` |
| 超时 | 节点不通或 DNS 未走代理 | 先 `curl -x $PROXY https://api.ipify.org` 确认出口 |
