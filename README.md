# Agent Skills · 真实踩坑版

一份自用的 Agent 技能集合（Claude Code / Codex / Hermes 通用格式）。
不是教程汇总，**每一条都来自实际项目里踩过的坑**：带具体参数、实测数据、失败样本，以及「为什么这么做」的原因。

> 全部 10 个技能脱敏后公开。原始版本在我自己的机器上跑，这里替换掉了店铺名、内部路径、账号常量。

## 这些技能解决什么

AI Agent 的通病是「会说不会做」：给它一个任务，它能写出一堆看起来对的代码，但一落到真实环境就崩——编码错了、接口返回乱码、文件传不上去、剪映把草稿加密了。

这份集合记录的都是那类**「不踩一遍根本想不到」的问题**：

| 技能 | 解决的真问题 |
|:--|:--|
| `qqbot-media-delivery` | 机器人发文件有 5MB 硬上限，而且 500 是间歇性的，不是网络问题 |
| `winforms-gui-tool` | 中文路径不是问题，**没有 BOM 的 .ps1** 才是；写完必须转 UTF-8 BOM |
| `mini-vpn-client` | 同一个订阅链接换 UA 就 403；切节点要传 UTF-8 字节否则静默失败 |
| `jianying-draft-automation` | 剪映 11.7 打开过的草稿会搬进 `Timelines/<UUID>/` 并加密成 base64 |
| `douyin-lyric-video` | 歌词视频的字幕位置、结尾帧、逐句对齐的完整流程 |
| `windows-operations` | 在 WSL 里操作 Windows：截不到窗口、抓不到前台、中文全乱码的解法 |
| `single-file-mobile-app` | 单文件 HTML App：先规划后写码、手机端验证、交付形态 |
| `parcel-tracking` | 免费快递接口会返回**互相矛盾**的三套轨迹，不能当准 |
| `subagent-team` | 派活给子代理：任务模板、验收清单、怎么不被「跑偏」 |
| `third-party-skill-install` | 装第三方技能：认结构、防炸索引、验证真的装上了 |

## 结构

```
skills/<技能名>/
  SKILL.md          # 主文件（frontmatter + 触发条件 + 步骤 + 坑）
  scripts/          # 可执行脚本（有的话）
  references/       # 参考资料（有的话）
```

## 怎么用

**Claude Code / Codex / Hermes Agent**：把 `skills/` 下想要的目录拷进你的技能目录，重启会话即可。

```bash
cp -r skills/qqbot-media-delivery ~/.claude/skills/
```

**只想抄思路**：直接读 `SKILL.md`，每个技能都按「什么时候用 → 怎么做 → 踩过什么坑」组织，不需要装。

## 说明

- 示例里的账号常量、路径、openid 都换成了占位符（`<OPENID>`、`<项目目录>`），用的时候按自己环境回填。
- 涉及平台自动化的部分是**记录做法**，不建议用来绕过平台规则。
- 有隐私或安全影响的内容（密码、密钥、客户信息）已全部剔除。

## License

MIT
