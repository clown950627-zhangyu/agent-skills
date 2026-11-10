# OpenClaw (真维斯) QQ Bot 配置参考

## 背景

真维斯 = OpenClaw 框架，跑在 Windows 主机上。不同于 Hermes Agent（小爱）原生支持 QQ Bot Gateway，OpenClaw 通过**官方 QQ 机器人插件**接入，需要在 `~/.openclaw/openclaw.json` 中独立配置。

## 前提 — 注册 QQ 机器人

1. 访问 [QQ 开放平台](https://q.qq.com/)（用用户的 QQ 号登录）
2. 完成开发者认证（个人/企业皆可，企业认证权限更高）
3. 创建机器人 → 填写名称、简介、头像 → 提交审核
4. 审核周期 1-7 个工作日，期间可用沙箱模式测试
5. 审核通过后，在机器人管理页面的「开发设置」获取：
   - **AppID**：一串数字，如 `102840596`
   - **Client Secret / AppSecret**：只显示一次，妥善保管

## 配置文件

编辑 `C:\Users\<用户名>\.openclaw\openclaw.json`，在 `channels` 中添加：

```json
{
  "channels": {
    "qqbot": {
      "enabled": true,
      "appId": "<AppID>",
      "clientSecret": "<ClientSecret>"
    }
  }
}
```

> ⚠️ 字段名是 **`qqbot`**（不是 `qq`），这是插件的标识名称。

### 插件安装

桌面文档推荐安装社区版：
```
openclaw plugins install @tencent-connect/openclaw-qqbot@latest
```

但实测官方版 `@openclaw/qqbot` 也可以工作（v2026.5.7），两者都走 QQ Bot API。

### 用 `channels add` 命令配置（替代手动编辑）

```
openclaw channels add --channel qqbot --token "<AppID>:<ClientSecret>"
```

其中 `--token` 格式为 `AppID:ClientSecret`。

## Gateway 启动流程

### 正确的启动命令

```bash
# Gateway 命令（不是 openclaw serve！）
"C:\Program Files\nodejs\node.exe" --max-old-space-size=4096 --max-semi-space-size=64 "C:\Users\<用户名>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway --port 18789
```

### 从 WSL 启动的正确方法

由于 WSL 的 UNC 路径问题，cmd.exe 不能直接在 `\\wsl.localhost\...` 目录运行。必须：

```bash
# 方法1：前台运行（推荐调试用）
cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "C:\Users\<用户名>\Desktop\run-gateway.bat"

# 方法2：WSL 后台进程
# 使用 terminal(background=true) 跑上述命令
```

### 批处理文件模板

```batch
@echo off
cd /d "C:\Users\<用户名>\.openclaw"
set "TMPDIR=C:\Users\<用户名>\AppData\Local\Temp"
set "OPENCLAW_GATEWAY_PORT=18789"
set "OPENCLAW_SYSTEMD_UNIT=openclaw-gateway.service"
set "OPENCLAW_WINDOWS_TASK_NAME=OpenClaw Gateway"
set "OPENCLAW_SERVICE_MARKER=openclaw"
set "OPENCLAW_SERVICE_KIND=gateway"
set "OPENCLAW_SERVICE_VERSION=2026.4.27"
start /B "" "C:\Program Files\nodejs\node.exe" --max-old-space-size=4096 --max-semi-space-size=64 "C:\Users\<用户名>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway --port 18789
```

### ❌ 常见误区

`openclaw serve` **不是有效命令！** 桌面上的 `start-openclaw.bat` 使用了不存在的命令：
```
openclaw serve --port 3000 --host 0.0.0.0  ❌ 会报错 Unknown command: serve
```
必须用 `openclaw gateway` 或直接调用 node 运行 gateway index。

## 从远程浏览器配置 QQ Bot 的局限

当使用 Hermes Agent 的 `browser` 工具（Browserbase 等远程浏览器服务）访问 QQ 开放平台时，有以下局限：

### QR 码登录不可用

QQ 安全机制**禁止从相册/截图识别二维码**。远程浏览器生成的 QR 码，即使用户手机 QQ 扫描相册截图，也会报错：
> "为了保证你的账号安全，本次请求不支持图片识别或长按扫描二维码授权，请通过摄像头扫一扫重新授权登录。"

**解决方式：**
1. **让用户用自己的手机/电脑浏览器打开 q.qq.com**，QQ 会自动授权登录（已在 QQ 客户端中登录的话）
2. 用户登录后截屏/分享链接给 Agent，Agent 接着操作
3. 密码登录（如果用户愿意提供凭证）

### 已验证的远程操作流程

```
1. Agent 在远程浏览器打开 q.qq.com
2. 无法扫码 → 请用户自己在手机上打开 q.qq.com
3. 用户登录后 → 截图发给 Agent → Agent 指导操作
4. 或用户分享具体页面 URL 给 Agent → Agent 分析页面内容
```

## 机器人管理页面说明

用户成功登录后，在「机器人列表」页面可以看到：
- 已创建的机器人卡片（如"真维斯"）
- AppID（如 <AppID>）
- AppSecret（以 **** 显示，有点击"查看"按钮）
- 操作按钮：**发起聊天** / **删除**
- 群聊权限设置在机器人详情页面的"功能设置"中

## 检查 Gateway 是否运行

```powershell
# 检查进程
<C盘>/Windows/System32/tasklist.exe 2>/dev/null | grep node

# 检查端口监听
<C盘>/Windows/System32/netstat.exe -ano 2>/dev/null | grep 18789

# 杀死旧进程
<C盘>/Windows/System32/taskkill.exe /F /PID <PID>
```

## 验证 QQ Bot 连接状态

### 查看日志

Gateway 启动后，QQ Bot 的连接日志在：
```
C:\Users\<username>\AppData\Local\Temp\openclaw\openclaw-YYYY-MM-DD.log
```

关键日志行示例：

| 日志 | 含义 |
|------|------|
| `http server listening (7 plugins: browser, device-pair, file-transfer, memory-core, phone-control, qqbot, talk-voice; 6.4s)` | Gateway 正常启动，QQ Bot 插件已加载 ✅ |
| `agent model: deepseek/deepseek-v4-flash (thinking=off, fast=off)` | Agent 模型已配置 ✅ |
| `[qqbot:default] Starting gateway — appId=xxx, enabled=true, name=unnamed` | 开始连接 QQ 平台 |
| `[default] ✅ Access token obtained successfully` | **连接成功！** 腾讯平台验证通过 ✅ |
| `[qqbot:api] <<< Status: 200 OK | TraceId: xxx` | QQ Bot API 请求成功 |
| `service-mode: cleared X stale gateway pid(s) before bind on port XXXXX` | Gateway 自动清理了之前残留的陈旧进程（自愈机制）⚠️ 正常行为，非错误 |
| `Connecting to wss://api.sgroup.qq.com/websocket` | 正在建立 WebSocket 长连接 |
| `WebSocket connected` | **WebSocket 连接已建立** ✅ |
| `[qqbot:token:xxx] Background refresh started` | Token 自动刷新机制已启动 |
| `[qqbot:default] Gateway ready` | **QQ Bot 通道就绪！** ✅ |
| `gateway ready` | Gateway 主服务就绪（无前缀日志）|
| `agent runtime plugins pre-warmed in XXXms` | 插件预热完成 |
| `[default] Connection failed: Failed to get access_token: {"code":100016,"message":"invalid appid or secret"}` | ❌ 腾讯平台不认凭证 |
| `startup model warmup timed out after 5000ms` | ⚠️ 正常警告，不影响运行 |

## 调试 QQ Bot 连接失败（核心调试流程）

### 错误码 100016 — invalid appid or secret

这是腾讯 QQ 开放平台返回的错误，**不是 OpenClaw 的问题**。凭证无效的原因：

1. **Bot 未在 q.qq.com 上创建** — AppID 可能根本不存在
2. **Client Secret 已过期或被重新生成** — QQ 开放平台可以随时重新生成密钥
3. **Bot 已删除或下线** — 机器人可能被从平台删除
4. **审核未通过** — 但未通过的 Bot 也应该能在沙箱模式使用

### 恢复流程

```
1. 打开 https://q.qq.com/
2. 用用户的 QQ 登录
3. 找到对应机器人 → 开发设置
4. 检查 AppID 是否正确
5. 重新生成 Client Secret（如果找不到了）
6. 复制新凭证 → 更新 openclaw.json
7. 重启 Gateway → 验证
```

### models.json — API Key 占位符问题

`agents/main/agent/models.json` 中 DeepSeek 的 `apiKey` 默认可能是占位符 `"DEEPSEEK_API_KEY"`，需要替换为真实密钥：

```json
"deepseek": {
  "baseUrl": "https://api.deepseek.com",
  "apiKey": "<KEY>",  // ← 替换此处
  ...
}
```

实际密钥存在 `agents/main/agent/auth-profiles.json` 中：

```json
{
  "profiles": {
    "deepseek:default": {
      "type": "api_key",
      "provider": "deepseek",
      "key": "<KEY>"
    }
  }
}
```

⚠️ 如果 models.json 的 `apiKey` 是占位符字符串而非真实密钥，Agent 调用模型时会失败。

### 已知凭证记录

| Bot AppID | Client Secret | 状态 | 备注 |
|-----------|--------------|------|------|
| **<AppID>** | （在 openclaw.json 的 channels.qqbot 中配置） | ✅ **当前活跃**（2026-06-19 验证） | 新 Bot，Gateway 自 17:57 运行中，Access token 获取成功，WebSocket 已连接 |
| <AppID> | ~~<ClientSecret>~~ → <ClientSecret> | ❓ 未知（上次确认 2026-05-10） | 原"真维斯"Bot，配置已被新 Bot 覆盖 |
| <AppID> | <ClientSecret> | ❌ 无效（2026-05-10） | credential-backup.json（曾于 2026-05-01 运行成功过，但已过期） |

> ⚠️ 每次重启 Gateway 时，`service-mode` 会自动杀死此前残留的陈旧 gateway 进程（日志可见 `killing 1 stale gateway process(es) before restart: <PID>`）。无需手动清理旧进程。

`credential-backup-default.json` 路径：`%USERPROFILE%\\.openclaw\\qqbot\\data\\credential-backup-default.json`

### `channels add` 命令（推荐替代手动编辑）

```bash
# 在 Windows cmd 中执行
openclaw channels add --channel qqbot --token "<AppID>:<ClientSecret>"
```

`--token` 格式为 `AppID:ClientSecret`。执行后会自动更新 `openclaw.json` 并备份旧配置到 `.bak` 文件。

从 WSL 调用：
```bash
cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "C:\Users\<user>\AppData\Roaming\npm\openclaw.cmd channels add --channel qqbot --token \"AppID:ClientSecret\""
```

成功输出：`Added QQ Bot account "default".`

### 环境变量认证（备选方案）

QQ Bot 插件也支持通过环境变量注入凭证，在 plugin manifest 中定义为：
- `QQBOT_APP_ID`
- `QQBOT_CLIENT_SECRET`

如果 `openclaw.json` 的 `channels.qqbot` 中没有找到凭证，插件会 Fallback 到环境变量。

## 从 WSL 完整配置流程（本会话验证成功）

```bash
# 1. 杀死旧进程
<C盘>/Windows/System32/taskkill.exe /F /FI "IMAGENAME eq node.exe"

# 2. 执行 channels add（配置新凭证）
cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "C:\Users\<用户名>\AppData\Roaming\npm\openclaw.cmd channels add --channel qqbot --token \"<AppID>:<ClientSecret>\""

# 3. 启动 Gateway
cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "C:\Users\<用户名>\Desktop\run-gateway.bat"

# 4. 监控日志确认连接状态
tail -f "<C盘>/Users/<用户名>/AppData/Local/Temp/openclaw/openclaw-$(date +%Y-%m-%d).log" | grep -i qqbot
```

### known-users.json — 过去成功交互过的用户

路径：`%USERPROFILE%\.openclaw\qqbot\data\known-users.json`

记录了所有跟 Bot 互动过的 QQ 用户，可用于确认 Bot 是否曾正常工作。

## OpenClaw 目录结构速查

```
%USERPROFILE%\.openclaw\
├── openclaw.json              # 主配置（含渠道、插件、模型）
├── openclaw.json.bak          # 配置备份
├── gateway.cmd                # Gateway 启动脚本（旧版）
├── plugins/
│   └── installs.json          # 已安装的插件记录
├── npm/node_modules/
│   └── @openclaw/qqbot/       # QQ Bot 插件的实际代码
├── agents/main/agent/
│   ├── auth-profiles.json     # API 密钥存储（如 DeepSeek sk-xxx）
│   ├── auth-state.json        # 认证状态记录
│   └── models.json            # 模型列表及配置
├── qqbot/
│   ├── data/
│   │   ├── credential-backup-default.json  # QQ 凭证备份
│   │   └── known-users.json                # 历史交互用户
│   └── sessions/              # QQ Bot 会话文件
├── logs/
│   ├── config-audit.jsonl     # 配置审计日志
│   └── config-health.json     # 配置健康检查
├── memory/                    # 真维斯的记忆
└── sessions/                  # OpenClaw 会话数据
```

## 重启 Gateway

OpenClaw Gateway 采用 service-mode 运行，具有内置的陈旧进程自愈机制：

```bash
# 从 WSL 调用（推荐用批处理文件）
cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "C:\\Users\\<user>\\Desktop\\run-gateway.bat"

# 或直接杀死旧进程后重启
<C盘>/Windows/System32/taskkill.exe /F /PID $(tasklist.exe 2>/dev/null | grep node | awk '{print $2}')
```

### ⚙️ Service-mode 自愈机制

当启动 Gateway 时，如果 18789 端口已被之前的陈旧进程占用，Gateway **会自动终止旧进程**并绑定端口：

```
[restart] killing 1 stale gateway process(es) before restart: 9948  ← 自动杀旧
[gateway] service-mode: cleared 1 stale gateway pid(s) before bind on port 18789  ← 确认清理
```

这意味着：
- 即使重复启动 Gateway，也不会出现端口冲突
- 旧网关进程会被自动清理，不需要手动 taskkill
- 日志中看到 "killing stale gateway" 是正常行为，不是错误
- 启动过程中可能看到两次完整的初始化序列（第一次被第二次杀掉）

### 📋 日志格式说明

OpenClaw 的日志文件是 **JSON 每行一条** 格式，而非纯文本：

```json
{"0":"{\"subsystem\":\"gateway\"}","1":"gateway ready","time":"2026-06-19T17:57:56.590+08:00",...}
```

每条日志包含 `time`（北京时间+08:00）、`message`（关键信息）、`logLevelName`（INFO/WARN/ERROR）。关键信息在 `message` 字段中。

### 查看日志的实用命令

```bash
# 查看今日日志的最后 100 条
tail -100 "<C盘>/Users/<user>/AppData/Local/Temp/openclaw/openclaw-$(date +%Y-%m-%d).log"

# 提取所有 message 字段（更快阅读）
grep -o '"message":"[^"]*"' "<C盘>/Users/<user>/AppData/Local/Temp/openclaw/openclaw-$(date +%Y-%m-%d).log" | head -50

# 只看 qqbot 相关
grep -o '"message":"[^"]*"' "<C盘>/Users/<user>/AppData/Local/Temp/openclaw/openclaw-$(date +%Y-%m-%d).log" | grep -i qqbot

# 只看错误和警告
grep '"logLevelName":"WARN\|ERROR"' "<C盘>/Users/<user>/AppData/Local/Temp/openclaw/openclaw-$(date +%Y-%m-%d).log"
```

## QQ 开放平台远程操作限制

从远程浏览器（Browserbase 等）操作 QQ 开放平台时：

### QR 码扫码登录陷阱

QQ 安全机制**禁止相册/截图识别二维码**，只能摄像头实时扫描。远程浏览器生成的 QR 码截图发给用户后：
- ❌ 用户用 QQ 扫相册截图 → 报错："不支持图片识别或长按扫描二维码授权"
- ✅ 处理方式：让用户**自己在手机上打开 q.qq.com** → 手机会自动通过 QQ 授权登录 → 用户截图分享页面

### 已知管理页面 URL

| 页面 | URL |
|------|-----|
| 机器人列表（登录后） | `https://q.qq.com/qqbot/openclaw/` |
| 开放平台首页 | `https://q.qq.com/` |
| 帮助文档（部分404） | `https://q.qq.com/wiki/` |

### 群聊权限的真相（重要）

**QQ 开放平台没有简单的「开启群聊」开关。** 机器人的群聊能力是：

1. **通过平台审核/上架流程获取的** — 不是设置里的一个 toggle
2. 需要填写机器人的**功能说明和使用场景**，提交审核
3. 审核周期 1-7 个工作日
4. 审核通过后，用户才能在 QQ 群设置里搜索添加该机器人
5. 审核期间可以用**沙箱模式**测试（但只有指定测试用户可用）
6. 如果机器人有明确的聊天/客服场景，可以以此申请群聊

所以无法拉群 ≠ 配置问题，是 QQ 平台审核流程的问题。

### 绕过方法

**【推荐】由小爱中转而非拉群：**
建一个普通 QQ 群，只把【小爱（Hermes）】拉进去（如果她的 Bot 已开通群聊权限），
用户在群里 @小爱 → 小爱 delegate 任务给真维斯执行 → 结果汇总回复。
不需要真维斯的 Bot 进群，也能统一指挥三 AI。

## 私聊与群聊

| 模式 | 说明 |
|------|------|
| **私聊** | 用户在 QQ 搜索机器人 → 点击开始私聊。Session: `agent:<agentId>:qqbot:user:<userId>` |
| **群聊** | 需要在 QQ 群设置中手动添加机器人。默认需要 **@机器人** 才会触发回复。Session: `agent:<agentId>:qqbot:group:<groupId>` |

## QQ 平台特殊限制 ⚠️

这是平台层面的硬限制，OpenClaw 无法绕过：

| 限制 | 说明 | 应对 |
|------|------|------|
| **不能发 URL** | 包含 URL 的消息会被静默过滤或拒绝发送 | 让 AI 描述内容而不发链接，用文字描述搜索关键词让用户自行搜索 |
| **消息格式有限** | ✅ 纯文本/图片/@用户/表情 ❌ Markdown/富文本卡片/URL | 在 Agent 提示词中声明"在 QQ 平台不要发送 URL 和 Markdown" |
| **消息长度限制** | 单条消息有长度限制 | OpenClaw 会自动分割长消息为多条 |
| **主动消息限制** | 需要用户先发消息给机器人，才能在窗口期内回复 | 超时窗口的主动消息（如 heartbeat、定时通知）可能被拒绝 |
| **调用频率限制** | 取决于认证级别 | 企业认证配额更高 |

## 从 WSL 配置真维斯的流程（完整版）

```bash
# 1. 找到配置文件并检查当前内容
cat <C盘>/Users/<user>/.openclaw/openclaw.json

# 2. 检查插件安装状态
cat <C盘>/Users/<user>/.openclaw/plugins/installs.json | grep qqbot

# 3. 编辑配置文件（修改 channels.qqbot 的 appId 和 clientSecret）
# 注意路径中的正斜杠和反斜杠

# 4. 用批处理文件启动 Gateway
cat > <C盘>/Users/<user>/Desktop/run-gateway.bat << 'EOF'
@echo off
cd /d "C:\Users\<user>\.openclaw"
set "TMPDIR=C:\Users\<user>\AppData\Local\Temp"
set "OPENCLAW_GATEWAY_PORT=18789"
set "OPENCLAW_WINDOWS_TASK_NAME=OpenClaw Gateway"
start /B "" "C:\Program Files\nodejs\node.exe" --max-old-space-size=4096 --max-semi-space-size=64 "C:\Users\<user>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway --port 18789
EOF

# 5. 确保 CRLF 换行
sed -i 's/$/\r/' <C盘>/Users/<user>/Desktop/run-gateway.bat

# 6. 运行
cd /mnt/c && <C盘>/Windows/System32/cmd.exe /c "C:\Users\<user>\Desktop\run-gateway.bat"

# 7. 确认进程运行
<C盘>/Windows/System32/tasklist.exe 2>/dev/null | grep node

# 8. 检查 QQ Bot 连接日志
tail -20 "<C盘>/Users/<user>/AppData/Local/Temp/openclaw/openclaw-$(date +%Y-%m-%d).log" 2>/dev/null

# 9. 如果看到 "invalid appid or secret" → 去 q.qq.com 更新凭证
```

## 注意事项

- QQ Bot 和真维斯各自有独立的 Bot QQ 号（需要不同的 QQ 机器人凭证）
- 小爱（Hermes）和真维斯（OpenClaw）是两个独立的 AI 系统，QQ 聊天记录不会自动同步
- 如需在 QQ 上统一指挥三 AI，最佳方案是：**用户在 QQ 找小爱，小爱 delegate 任务给真维斯，结果汇总返回**
- `start` 命令在批处理中：第一个参数是窗口标题（用空字符串 `""`），第二个是程序路径。路径含空格时必须用引号
- 从 WSL 调用 cmd.exe 时，用 `cd /mnt/c &&` 前置避免 UNC 路径问题
