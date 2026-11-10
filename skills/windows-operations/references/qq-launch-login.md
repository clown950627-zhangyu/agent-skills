# QQ 启动与登录交接 — Session 细节（2026-07-28）

任务：用户从 WSL 发起 "帮我打开QQ并登录"。

## 验证过的完整流程

1. 找快捷方式：
   `Get-ChildItem 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs' -Recurse -Filter '*QQ*'`
   → `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\腾讯软件\QQ\QQ.lnk`
   （控制台里"腾讯软件"显示为乱码——只是管道编码问题，不影响操作。）

2. COM 解析快捷方式目标：
   `$ws = New-Object -ComObject WScript.Shell; $lnk = $ws.CreateShortcut('...\QQ.lnk'); $lnk.TargetPath`
   → `C:\Program Files\Tencent\QQNT\QQ.exe`

3. 启动：`Start-Process 'C:\Program Files\Tencent\QQNT\QQ.exe'`

4. 验证：`tasklist /FI "IMAGENAME eq QQ.exe"` → 出现 4 个 QQ.exe 进程（PID 每次不同）。
   多进程 = 正常（主进程 + 渲染进程），不是启动失败。

5. 截屏（SKILL.md §3 的 DPI 感知脚本，物理分辨率 3000x2000）→ `vision_analyze`：
   观察到 QQ NT 快速登录界面：已保存账号"工常宝盖鱼"、蓝色"登录"按钮、
   "账号登录"/"注册账号"链接、未勾选的"自动登录"圆圈。

6. 交接：用户自己点"登录"。Agent 无法点击（WSL 无鼠标控制），
   且按策略凭证操作必须用户本人完成。

## 登录窗口状态 → 用户动作对照表

| 状态 | vision 看到什么 | 用户要做的 |
|---|---|---|
| 快速登录 | 账号名 + 单个蓝色登录按钮 | 点登录（可先勾选自动登录） |
| 二维码 | 二维码方块 | 用手机 QQ 扫码（拍屏幕的二维码会被拒绝） |
| 密码表单 | 账号登录输入框 | 手动输入凭证 |

## 时序注意

QQ NT 从 Start-Process 到登录窗口渲染完成需要约 5–10 秒。
太早截屏只会看到桌面/终端，误判为启动失败。
