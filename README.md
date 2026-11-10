# Agent Skills · 真实踩坑版

一套在实际项目里跑出来的 AI Agent 技能（Claude Code / Codex / Hermes Agent 通用格式）。

**不是教程汇编。** 每一条都来自真实项目：带具体参数、实测数字、失败样本，以及「为什么必须这么做」。

> 全部技能已脱敏后公开：店铺名、内部路径、账号常量都换成了占位符。


## 为什么值得看

AI 写代码的通病是「看着对、一跑就崩」——编码错了、接口返回乱码、文件传不上去、工具把草稿加密了。

这份集合记录的全是那类 **不踩一遍根本想不到** 的问题。每个技能都按同一套结构写：

```
什么时候用（触发条件） → 怎么做（可执行步骤） → 踩过什么坑（具体报错和对策）
```


## 技能清单

| 技能 | 解决什么问题 | 目录 |
|:--|:--|:--|
| **qqbot-media-delivery** | 通过 QQ 机器人通道把音频/视频/文档真正发到用户手机上时读。含富媒体接口、大小上限与压缩策略。 | [`skills/qqbot-media-delivery`](skills/qqbot-media-delivery/) |
| **windows-operations** | 在 WSL 里操作 Windows：截不到窗口、中文乱码、PowerShell 调用，全部有对策。 | [`skills/windows-operations`](skills/windows-operations/) |
| **winforms-gui-tool** | 把脚本做成双击就能用的 Windows 小窗口（WinForms + 便携打包）。 | [`skills/winforms-gui-tool`](skills/winforms-gui-tool/) |
| **mini-vpn-client** | 自建 Clash/mihomo 客户端时读。含订阅 UA 坑、PS 编码坑。 | [`skills/mini-vpn-client`](skills/mini-vpn-client/) |
| **jianying-draft-automation** | 用剪映批量出营销短视频（草稿生成/改文案/导出）必读 | [`skills/jianying-draft-automation`](skills/jianying-draft-automation/) |
| **douyin-lyric-video** | 做抖音/视频号歌词视频时使用。含用户钦定的字幕风格、结尾帧规范、歌词同步方法与完整流程。 | [`skills/douyin-lyric-video`](skills/douyin-lyric-video/) |
| **single-file-mobile-app** | 做自用单文件 HTML App（提醒/打卡/记录）时读。先规划后写码、内嵌图库、手机验证、交付。 | [`skills/single-file-mobile-app`](skills/single-file-mobile-app/) |
| **parcel-tracking** | 查快递/物流单号时读。含承运商识别、查询接口与「数据互相矛盾」的铁律。 | [`skills/parcel-tracking`](skills/parcel-tracking/) |
| **subagent-team** | 派活给子代理、只做对接与验收时读。角色分工、任务模板、验收清单。 | [`skills/subagent-team`](skills/subagent-team/) |
| **third-party-skill-install** | 用户发来 GitHub 仓库/榜单让“装上”时读。取包、认结构、链接、防炸索引、验证。 | [`skills/third-party-skill-install`](skills/third-party-skill-install/) |

## 每个技能踩过的坑（原文摘录）

下面是各技能里记录的真实坑，按技能分组。想抄作业直接看这里。


### qqbot-media-delivery

- 中文文件名：发给 QQ 前复制成纯 ASCII 文件名（如 youguang_chorus.mp3），中文路径/文件名在部分环节会静默失败
- 别把 token 写日志/回显；调试时只打印长度或前 4 位
- msg_seq 递增，同一 msg_seq 连发可能被去重


### winforms-gui-tool

- .ps1 里 $_／$env: 通过 bash 传参会先被 bash 吃掉 → 逻辑写进 .ps1，用 -File 调。
- Add-Type 的 C# 块要大写最小：struct 放类外、每个块只放用到的 DllImport，否则报 <class> was not found，像是逻辑错。
- ShowDialog() 阻塞到窗口关闭，后面的代码不会跑；需要定时刷新用 Timer。


### douyin-lyric-video

- overlay 必须加 -t {时长} + shortest=1 — 否则无限渲染·文件膨胀到 826MB
- 单图/结尾帧用 -frames:v N 限制 — 不要把 -t 放在 -i 前面（会导致 zoompan 无限输出→100秒）
- 字幕 PNG 裁条状（y=560~760）— 全屏 PNG overlay 极慢（20分钟跑不完）


### single-file-mobile-app

- 用药/次要卡片占首屏太大 → 训练页主体必须是训练，次要信息折叠或降到底部。
- 浏览器工具的文件路径：browser_exec 的 Chrome 在 WSL 里跑，file:///C:/... 会返 ERR_FILE_NOT_FOUND。先把文件 shutil.copy 到 /tmp/ 再用 file:///tmp/...。
- 进度条太淡 会被当成普通分隔线 → 进度值同时给文字数字。


### subagent-team

- tool_call 的 name 必须是工具名（cronjob_manage），任务名写在 arguments.name 里；
- 子代理不能调用 delegate_task / clarify / memory / cronjob —— 需要二次分派的活不能给它
- 子代理进程会随会话结束被杀 —— 要活过这次对话的（定时任务、长跑服务）走 cronjob 或 terminal background，不要派


## 安装

把想要的目录拷进你的技能目录，重启会话即可。

```bash
# Claude Code
cp -r skills/qqbot-media-delivery ~/.claude/skills/

# Codex CLI
cp -r skills/qqbot-media-delivery ~/.codex/skills/
```

只想抄思路？直接读 `skills/<名字>/SKILL.md`，每个都是自包含的，不用装。


## 目录结构

```
skills/<技能名>/
  SKILL.md         主文件（frontmatter + 触发条件 + 步骤 + 坑）
  scripts/         可执行脚本（部分技能有）
  references/      参考资料（部分技能有）
```


## 说明

- 示例里的账号常量、路径、openid 均为占位符（`<OPENID>`、`<项目目录>`），按自己环境回填。

- 涉及平台自动化的内容是 **记录做法**，不用于绕过平台规则。

- 有隐私或安全影响的内容（密码、密钥、客户信息）已全部剔除。


## License

MIT
