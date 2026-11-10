---
name: qqbot-media-delivery
description: 通过 QQ 机器人通道把音频/视频/文档真正发到用户手机上时读。含富媒体接口、大小上限与压缩策略。
version: 1.0.0
author: 小爱
license: MIT
metadata:
  hermes:
    tags: [qqbot, 文件交付, 富媒体, 音视频]
    related_skills: [douyin-lyric-video, media-output-sanity-check]
---

# QQ 机器人交付文件（音频/视频/文档）

## When to Use

用户说「把文件发我」「做成 mp3/mp4 发给我」「我不在电脑旁，你自己想办法」时。

**先认清一件事**：回复里写 `MEDIA:/path` 对**图片**基本能落地，对 **mp3 / mp4 / 文档并不可靠**——
用户会回「给我 mp3 文件」，说明附件没到。别再重复贴 MEDIA 标签，直接走下面的富媒体接口。

---

## 一、直调 QQ 开放平台富媒体接口（唯一稳的路径）

凭据就在本机 `~/.hermes/.env`：`QQ_APP_ID`、`QQ_CLIENT_SECRET`。
**只读进内存，不打印、不写进业务库文件**。

```python
import json, base64, urllib.request

# 0) 读凭据
def load_env(p="/home/clown_zy/.hermes/.env"):
    e = {}
    for line in open(p, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e

APP_ID     = load_env()["QQ_APP_ID"]
APP_SECRET = load_env()["QQ_CLIENT_SECRET"]
OPENID     = "<对方的 openid>"        # 就是消息来源里的 user_id / openid

# 1) 取 access_token（有效期约 2 小时）
req = urllib.request.Request(
    "https://bots.qq.com/app/getAppAccessToken",
    data=json.dumps({"appId": APP_ID, "clientSecret": APP_SECRET}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
TOKEN = json.loads(urllib.request.urlopen(req, timeout=60).read())["access_token"]

# 2) 上传富媒体
raw = open("/path/to/file.mp4", "rb").read()
body = {"file_type": 2,                                   # 1图片 2视频 3语音 4文件
        "file_data": base64.b64encode(raw).decode(),
        "srv_send_msg": False}
up = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"https://api.sgroup.qq.com/v2/users/{OPENID}/files",
    data=json.dumps(body).encode(),
    headers={"Authorization": f"QQBot {TOKEN}", "Content-Type": "application/json"},
    method="POST"), timeout=180).read())

# 3) 发出去（msg_seq 每轮递增，别复用）
sent = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"https://api.sgroup.qq.com/v2/users/{OPENID}/messages",
    data=json.dumps({"msg_type": 7, "media": {"file_info": up["file_info"]},
                     "content": "", "msg_seq": 1}).encode(),
    headers={"Authorization": f"QQBot {TOKEN}", "Content-Type": "application/json"},
    method="POST"), timeout=60).read())
print(sent.get("id"))          # 有 message id 才算真发出去
```

`file_type`：**音频用 3、视频用 2、普通文件用 4**。实测 mp4 用 2 能过、mp3 用 4 能过。

---

## 二、大小上限（必踩，且**按 file_type 不同**）

- 实测 **音频 1.19 MB（base64 后 1.5 MB，file_type=4）→ HTTP 500 `call inner proxy error` (code 850012)**
- 实测 **音频 716 KB（base64 后 955 KB）→ 成功**
- 实测 **视频 5.19 MB（base64 后 6.93 MB，file_type=2）→ 成功**

**结论：上限不是统一的「800 KB」，是分类型的。** 顺序永远是：**先用原生 file_type 直接怼一次**，
拿到 850012 再降档压缩 —— 视频能过 5 MB，音频 1 MB 都过不去，凭「反正都很大」提前压等于白掉画质/音质。
经验阈值：**视频可到 ~5 MB；PDF/文档实测 2.6 MB（base64 后约 3.5 MB，file_type=4）能过；音频保守按 800 KB 走**（再大没验过，超过 6 MB 先压）。

### 大文件首选：微信单文件（能一次发就不拆）

QQ 机器人单文件上限约 5MB；**拆片发给用户是下策——他会直接反问「不能一个文件吗」**。
所以 >5MB 的包先走微信整包发，QQ 分片只做兜底。
**先试微信通道**，同一个文件整包发，实测 25.5MB 一次过：

```bash
cd ~/projects/codex-wechat && \
  ~/.hermes/tools/node-26.12.1-linux-x64/bin/node sendfile.js "<C盘>/路径/pkg.zip" "一句话说明"
# 成功打印 FILE SENT (xx MB) + TEXT SENT
```

`sendfile.js` 已写好（`~/projects/codex-wechat/sendfile.js`），走 `sendWeixinMediaFile`，
自动传 CDN + 发文件消息 + 跟一条文字说明。前提仍是 **context_token 存在**（他最近给微信 bot 发过消息）。

顺序：**微信单文件 → 不行再 QQ 分片**。分片方案只在用户明确要留在 QQ 里、或微信窗口已关时用。

### 分片方案（QQ 兜底，实测口径）

zip/安装包这类 `file_type=4` 的文件，**单片上限约 5 MB**：

```
实测 file_type=4：5,242,880 字节（5.00MB）→ 成功
                  6,291,456 字节（6MB）    → HTTP 500
                  9 MB                     → HTTP 500
                  25.5MB 整个包            → 413 Request Entity Too Large
```

**而且 500 是间歇性的**：同一批 6 片，一轮下来 0/1/3 失败、2/4/5 成功；过几分钟原样重发六片全过。
所以一失败别换方案，**先退避重试**（失败后等 15·n 秒，最多 4 次）。

做法（Linux 切、Windows 合，用户只双击一次）：

```bash
split -b 5m -d -a 1 "pkg.zip" "pkg.zip.part"     # part0..partN
```

合并脚本必须**纯 ASCII + CRLF**，并把 `cd /d "%~dp0"` 写进去（双击时工作目录不一定是脚本所在处）：

```bat
@echo off
cd /d "%~dp0"
copy /b "pkg.zip.part0"+"pkg.zip.part1"+"pkg.zip.part2"+"pkg.zip.part3"+"pkg.zip.part4"+"pkg.zip.part5" "pkg_合并.zip"
if exist "pkg_合并.zip" (echo 合并完成) else (echo 合并失败，检查6个分片是否都在)
pause
```

交付时**给出每片确切字节数**（如 part0–4 = 5,242,880、part5 = 486,962、合并后 26,701,362），
用户才能认出重试时混进来的旧片；重跑 split 会让同名片内容不同，合并脚本换个名字（`合并_六段.bat`）
并明说「以这个为准，前面那个删掉」。

**多页 PDF 先压缩再发**（Chrome 导出的中文 PDF 带整套字形，动辄 3–4 MB）：

```python
import pymupdf
doc = pymupdf.open("deck.pdf"); doc.subset_fonts()
doc.save("deck_small.pdf", garbage=4, deflate=True, clean=True)   # 实测 3.4MB → 2.6MB
```

**演示稿两头交付**：先发 2–4 张关键页 PNG（`file_type=1`，手机上直接看得清），再发 PDF 供打印。
只发 PDF 的话，对方往往没耐心在手机里开附件。

音频降档（保住时长和完整性，只降码率）：

```bash
ffmpeg -y -v error -i in.mp3 -c:a libmp3lame -b:a 192k out.mp3   # 约 30 秒 → 700 KB
```

视频同理：`-c:v libx264 -crf 23 -r 30 -c:a aac -b:a 128k`，1080×1920 竖版 30 秒约 1 MB、
2 分 58 秒全曲约 5 MB（实测能过），**不必为了「求稳」先压到 720×1280**；只有真的被 850012 拒了才降。
**发过一版之后不要再重复发同内容**，直接在文字里说明「这是压缩版」。

---

## 三、备选：给他一个局域网直链

文件大又不想压时，起一个临时 HTTP 服务，把链接发他（手机同 WiFi 可直接点开下载）：

```bash
cd <C盘>/分享 && nohup python3 -m http.server 8080 --bind 0.0.0.0 >/tmp/share.log 2>&1 &
```

发链接前**自己先验证 200**：`http://127.0.0.1:8080/x.mp3` 与 `http://<局域网IP>:8080/x.mp3` 都要通
（Windows 侧 `Invoke-WebRequest` 测，别只信 WSL 里的 curl）。局域网访问依赖 portproxy 已指向当前 WSL IP ——
WSL 重启后 IP 会变，portproxy 会失效，详见 `windows-operations` 的 WSL 转发条目。

---

## 四、定时盯守：有变化才推图（cron + 截图脚本 + 本技能的一行发送）

用户说「你帮我盯着，有情况截图发我，我看了再给你指示」时，不要靠一直接着聊会话——
建一个 cron，每 10 分钟跑一次，只在**有实质变化**时发图。已验证可用的形状：

```python
# ~/.hermes/scripts/<watch>_cap.py —— cron 的 script 字段直接指它，stdout 注入 agent 上下文
PS = "<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
r = subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", r"C:\Windows\Temp\cap_target.ps1"],
                   capture_output=True, text=True, timeout=120)
print(f"path: <C盘>/Windows/Temp/target.png  size: {os.path.getsize(...)}")
```

```text
cronjob_manage create
  schedule: every 10m
  script:   <watch>_cap.py            # 先截图，路径进上下文
  continuity: true                    # 每轮能看到上轮输出 → 才能对比"变了没"
  deliver:  local                     # 别靠 cron 的 deliver 发图，主动发走下面的脚本
```

agent 的 prompt 里把「什么算有情况」写成白名单：**完成 / 报错或弹窗等人点 / 从干活变成等输入 / 关键数字或方案变更**，
**同一状态只报一次**；「计时长时间不动」不进白名单（后台跑长命令时 UI 本来就不刷新，报多了用户会连着追问「还卡着？」）。
其余一律只输出 `[SILENT]` 不发送；要发就一条命令：

```bash
python3 ~/.hermes/scripts/send_qq_media.py --image <C盘>/Windows/Temp/target.png \
        --text "【盯守 HH:MM】一句话结论"
```

`scripts/send_qq_media.py` 是本技能自带的现成脚本（默认发给用户私聊 openid，`--openid` 可换人），
cron 里直接用，不要每组重写 token/upload/send 三段。四个通道：

```bash
--image  → file_type=1   截图、单张图
--video  → file_type=2   mp4
--audio  → file_type=3   mp3/m4a
--file   → file_type=4    zip、pdf、xlsx、exe（给别人装的工具包走这个）
```

发**安装包/压缩包**（不用 --image）时先把中文目录打平再压：`Compress-Archive` 会把中文名写成
zip 内的 UTF-8 名，Windows 资源管理器解压正常，但部分国产解压工具会乱码——交付时顺手说一句
「解压后目录名可能显示为乱码，不影响运行」。

两条纪律：

- **建 cron 时不要传 `enabled_toolsets: []`** —— 空数组是「显式零工具集」，agent 会连截图/看图工具都没有，任务静默空转；要全量工具就别传这个字段。
- **盯第三方 agent 时默认只读**。除了用户明确说「你告诉他…」那一句，不点它的按钮、不代它作答。

### 盯桌面版 Codex（没有本地日志）

桌面版 Codex（ChatGPT 桌面应用）**不往本地写会话文件**，`~/.codex/sessions` 只有命令行版的。
唯一入口是画面：`PrintWindow(hwnd, hdc, 2)` 抓该窗口自己的位图再喂 vision_analyze。
`SetForegroundWindow` 会被前台锁拒（整屏截图里永远看不到它）；返回 `RECT=0,0` 说明窗口最大化，窗口坐标即屏幕坐标。

- 报 `{"detail":"Bad Request"}` = 服务端拒收请求（不是断网/没登录/没额度）。**先换代理节点再试**——
  实测美国1 → 美国2 就恢复；换节点无效才开新对话测（新对话能回＝旧对话上下文塌了）。
- 「Working for X 分」计时长时间不动 ≠ 卡死：后台跑长命令时 UI 本来不刷新。
  要判死活看进程 CPU 增量 / codex 子进程是否还在，别只看截图。
- 误报一次会被用户吐槽（「还卡着？」好几轮），同状态只报一次。

---

## 五、备用通道：微信（ilink）主动推送

用户说「QQ 我收得到，我要是不理就走微信」时，微信是**第二跳**，不是替代。
QQ 主动消息有窗口期和频次限制，真到要紧事被静默吞掉时，得有一条兜底路。

机制：复用本机常驻的 `codex-wechat`（`systemctl --user status codex-wechat` 应为 running），
它的微信登录态就在 `~/.codex-wechat/accounts/` 里，不用重新扫码。

```bash
cd ~/projects/codex-wechat && \
  ~/.hermes/tools/node-26.12.1-linux-x64/bin/node send.js "【小爱】一句话（时间）"
# 成功只打印 SENT
```

`send.js` 是现成的（`~/projects/codex-wechat/send.js`），内部走 `src/infra/weixin/api.js` 的
`sendMessage`，打的就是微信 ilink 的 `ilink/bot/sendmessage`。要自己重写时的最小请求体：

```json
{"msg": {"client_id": "<uuid>", "from_user_id": "", "to_user_id": "<他的 openid>",
 "message_type": 2, "message_state": 2,
 "item_list": [{"type": 1, "text_item": {"text": "正文"}}],
 "context_token": "<必须带上，否则发不出去>"}}
```

- `token` 在 `~/.codex-wechat/accounts/<accountId>.json`，`context_token` 在
  `<accountId>.context-tokens.json`（按对方 openid 索引）。**只读进内存，不打印、不贴日志。**
- **`context_token` 是硬门槛**：只有他最近给这个微信 bot 发过消息才有。缺它会直接报
  「没有 context_token，主动推送拉不起来」——这不是脚本坏了，是微信侧会话窗口没了，
  得让他先随便回一句，或退回 QQ。
- 返回 `SENT` 只代表**接口收下了**，不等于他手机响了。第一次用这条通道必须让他确认收到，
  没确认之前不要把它当可靠通道汇报。

### 升级规则（两条通道怎么配合）

```
第一跳   QQ      截图 + 一句话，正常情况只发这个
第二跳   微信    同一问题上一轮已经发过 QQ、这一轮还是没解决 / 他没动静 → 换微信催
大事件           跑完了 / 彻底报错不能用 → QQ 和微信各发一次
```

写进 cron 的 prompt 里，靠 `continuity` 拿上一轮输出来判断「这个问题是不是已经报过」。

---

## 六、坑

- **中文文件名**：发给 QQ 前复制成纯 ASCII 文件名（如 `youguang_chorus.mp3`），中文路径/文件名在部分环节会静默失败
- **别把 token 写日志/回显**；调试时只打印长度或前 4 位
- **`msg_seq` 递增**，同一 `msg_seq` 连发可能被去重
- **token 会短命（约 2 小时）**：上传时返回 `401 {"code":11244,"err_code":40011027}` = token 过期，
  **重新走一次 getAppAccessToken 再原样重试即可**，不要以为是接口或参数变了、更不要改 file_type 乱试
- **发完必须看返回 `id`**：只有 HTTP 200 但没 id，等于没发
- 大文件不要用 base64 硬怼：那是把内存和接口一起撑爆，先压
