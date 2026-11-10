---
name: winforms-gui-tool
description: 给他做 Windows 双击小工具（WinForms+便携打包）时读。
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [windows, gui, powershell, winforms, delivery]
    related_skills: [windows-operations, mini-vpn-client]
---

# Windows 桌面小工具（PowerShell WinForms）

## When to Use

他说「弄个界面」「双击就能用」「不想看黑窗口」「能不能点几下就切」，
或要一个能拷到别的电脑上安装的小工具（开关、面板、批量处理）时。
不适用：一次性命令、服务器上跑的脚本、已有现成 GUI 只需调用的场景。

适用：他要一个「能点、好看、双击就能用」的本机小工具（VPN 开关、服务开关、批量处理、配置面板），
而不是一行命令或一个黑窗口。零依赖，不装运行时，不写注册表，拷走就能在别的电脑上用。

## 形状（他要的样子）

```
深色底 #0F1114   面板 #16191F   电光青 #00E5FF   字 #E8EDF2   灰 #8A94A6
红 #FF5C5C（失败）   绿 #3DDC97（成功/运行中）
标题 18pt 粗体青色；状态灯一行（● 运行中 PID 1234）；主按钮青底黑字
固定窗口（FormBorderStyle=FixedSingle, MaximizeBox=$false），不做自适应
```

四条硬规则：

1. **一屏看完全部状态**：运行中/已停止、当前连接、关键数字，不要藏在子页面。
2. **主操作一个青色按钮**，其它一律深色面板底，不要让两三个按钮抢一样重的视觉。
3. **列表要有第二列数据**（延迟、大小、状态），空格子看着像坏了。
4. **不许弹黑窗口**：外层 `.vbs` 用 `sh.Run(cmd, 0, False)` 静默拉起。

## 文件四件套

```
<工具目录>\
  <名字>.ps1      GUI 主体（唯一需要改的文件）
  启动.vbs        WScript.Shell.Run("powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""<绝对路径>.ps1""", 0, False)
  安装.bat        双击 → 跑 install.ps1 → pause（纯 ASCII）
  install.ps1     复制整目录到 %LOCALAPPDATA%\<名字>\ + 建桌面快捷方式（TargetPath=wscript.exe，Arguments=".vbs 全路径"，IconLocation=主程序）
```

- 快捷方式用 `WScript.Shell.CreateShortcut`，**不写注册表、不装服务、不要求管理员**。
- 给别人电脑用：`Compress-Archive -Path <目录>\* -DestinationPath <目录>.zip`，把运行时/配置文件一起打进去，对方解压双击 `安装.bat` 就完事。
- 交付话术只要四行：拷 zip → 解压 → 双击安装.bat → 双击桌面图标。不解释实现。
- **发给他时别再拆片**：这类包带上内核就是 20MB+，而 QQ 机器人单文件上限约 5MB。
  拆成 part0..partN + 合并.bat 他能用但会直接反问「不能一个文件吗」——**先走微信单文件**
  （`~/projects/codex-wechat/sendfile.js`，25MB 整包一次过）， QQ 分片只在没有微信通道时兜底。
  详见 `qqbot-media-delivery`。

## 编码（不照做必炸）

| 文件 | 编码 | 写法 |
|:--|:--|:--|
| `.ps1` | UTF-8 **带 BOM** + CRLF | `open(p,"w",encoding="utf-8-sig",newline="\r\n")` |
| `.vbs` | UTF-16 LE 带 BOM（含中文路径时） | `open(p,"wb").write(b"\xff\xfe"+s.encode("utf-16-le"))` |
| `.bat` | 纯 ASCII（最稳） | 需要中文就 GBK，见 windows-operations §12 |

`write_file` 写出来的是 UTF-8 无 BOM，**每写完一个 .ps1 都要转一次 BOM**，否则中文按钮/标题直接语法错。

## 调接口的工具（VPN/HA/自建服务）

`Invoke-RestMethod` 把无 `charset` 的 JSON 按 Latin-1 解 → 中文名乱码，`-like` 永远不匹配。
一律读字节：`[System.Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray()) | ConvertFrom-Json`；
写回时 `-Body` 传 `UTF8.GetBytes($json)`。完整函数见 `windows-operations` §2。

## 写的时候

- **坐标手算，不用布局容器**。`Location`/`Size` 全写死，窗口固定尺寸，一次性对齐；改字体大小要连带改 y 偏移。
- **首屏必须有数据**：`Form.ShowDialog()` 之前先 `Refresh-Status` + 加载列表，不要等用户点「刷新」才看见东西。
- **默认选中项不能是第一个**。选业务上真正的主对象（名字带关键词的那个），选错会让人误操作。
- **耗时循环要分片刷新**：每 4 个跑一次 `$Form.Refresh()`，否则窗口假死。
- **禁用态要真的禁**：`$btn.Enabled = $false`（运行中就别让「开启」可点）。

## 交付前：从「安装后的副本」冷启动跑一遍

他说「你验证一下，必须能用」时，开发目录里那个窗口跑着不算数——那台机器上核心进程早就在跑了，
`Get-Process` 找到现成的就跳过启动逻辑，等于**启动路径一次都没测**。按这个顺序验：

```
① 解压 zip 到干净目录（C:\\Windows\\Temp\\<tool>_test）→ PSParser 语法检查解压出来的 .ps1
② 从解压目录跑 install.ps1 → 确认 %LOCALAPPDATA%\\<名字>\\ 有全套文件 + 桌面 .lnk 生成
③ 杀干净：Stop-Process 核心 + 按标题杀旧 GUI（这一步是「模拟新电脑」的关键）
④ 从**安装后的副本**启动 GUI → PrintWindow 截一张 → 必须显示「已停止」且主按钮可点
⑤ 点主按钮（按窗口 rect 偏移算坐标）→ 再截一张 → 必须变「运行中」+ 列表有数据
⑥ 验业务真的通：用工具启动的核心发一次真实请求（curl/Invoke-WebRequest 走它的端口），看返回码
```

第 ④ 步显示「运行中」就说明老进程没杀干净，验的是别人的进程，不是你的包。

**改过 `.ps1` 必须重新 `Compress-Archive`**：zip 是快照，改完不重打，发出去的就是上一版，
他装上看到的是旧界面（默认选中项、按钮文字全对不上）。重打包前先把文件夹里的 .ps1 确认是 BOM 版。

## 验收（看不到屏幕也能验）

真风险不是崩溃，是**窗口根本没出来**和**窗口在下面**——两者从 WSL 看一模一样。

```
① 语法：PSParser::Tokenize 只解析不执行 → 'SYNTAX OK' 才继续
② 进程：Get-Process powershell / wscript 是否有目标
③ 画面：PrintWindow(hwnd, hdc, 2) 抓该窗口自己的位图 → vision_analyze
   （SetForegroundWindow 会被前台锁拒，整屏截图里永远看不到它）
```

`vision_analyze` 里要逐项读：按钮齐不齐、列表空不空、中文有没有乱码、状态灯说什么。
看到他截图/说「看到了」只说明窗口存在，**不说明内容对**——自己抓一张再回话。

## 坑

- **`.ps1` 里 `$_`／`$env:` 通过 bash 传参会先被 bash 吃掉** → 逻辑写进 .ps1，用 `-File` 调。
- **`Add-Type` 的 C# 块要大写最小**：struct 放类外、每个块只放用到的 DllImport，否则报 `<class> was not found`，像是逻辑错。
- **`ShowDialog()` 阻塞到窗口关闭**，后面的代码不会跑；需要定时刷新用 `Timer`。
- **窗口盖住了不代表没启动**，先 PrintWindow，再考虑杀进程重启。
- **点击坐标一律按窗口 rect 换算，不要照搬截图上的像素**：截图会被 vision 降采样（1920→960 就是 2 倍）。
  写个 `-RelX/-RelY` 参数的点击脚本，内部 `GetWindowRect` + 偏移；窗口最大化时 rect 返回 `0,0`，相对坐标正好等于屏幕坐标。
  点击用 `SetCursorPos` + `mouse_event(0x0002)/(0x0004)`，别用 SendKeys 模拟——按钮不响应。
- **杀隐藏启动的 PowerShell 按标题匹配常常抓不到**（`-WindowStyle Hidden` 的宿主进程 `MainWindowTitle` 可能为空），
  改按「窗口标题枚举 + 该窗口所属 PID」来杀，否则你以为清了旧版，屏幕上跑的还是上一版。
- **改完 `.ps1` 必须重启窗口才生效**：`ShowDialog()` 跑的是启动时载入的脚本，
  你改了默认选中项、按钮文字，屏幕上那个还是旧的，验收会一直看到老版本。
  杀进程按窗口标题精确匹配（`Get-Process powershell | ? MainWindowTitle -like '*<工具名>*'`），
  不要 `Stop-Process -Name powershell` 一网打尽——会连带杀掉别的脚本。
- **打包时把运行时和配置目录一起打**（核心 exe、geoip、`configs\`、`config.yaml`），
  对方解压装完就能直接用；但配置里如果带订阅/节点/账号，**交付时明说一句「配置已经打在里面」**，
  否则他换电脑后不知道自己的订阅信息也被拷走了。

## 交付口径

回话只给：做好了什么功能、顺手修了什么坑、在别的电脑怎么装（四行）。
不贴代码、不讲 WinForms 原理、不列备选方案。
