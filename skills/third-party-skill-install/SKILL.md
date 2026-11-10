---
name: third-party-skill-install
description: 用户发来 GitHub 仓库/榜单让“装上”时读。取包、认结构、链接、防炸索引、验证。
version: 1.0.0
author: 小爱（Hermes）
license: MIT
tags: [skills, 安装, github, 索引管理]
metadata:
  hermes:
    tags: [skill安装, github, 上下文管理]
    related_skills: [find-skills, hermes-agent]
---

# 给 Hermes 装第三方 skill

## When to Use

用户发来 GitHub 链接或一张榜单图，说「装上」「都装了」「这个也装」。
或他自己用某个 skill 效果不好，要换/补一个。

## 〇、用户发的是「必装榜单」时：先评估，不要照着装

他会连发 2–3 张「自媒体/小红书必装的 N 个 skill」图（多数是自媒体号自己编的，名字对不上真仓库）。
**默认动作不是全装，是合并去重后逐个核对。**

```
① 三张榜合并去重（本次 24 项 → 去重后 ~19 个不同名字）
② 逐个比对本地已有（包括近似替代，不只看同名）：
   baoyu-* 全套 / guizang / viral-copywriter / excalidraw / content-strategy …
③ 剩下的才找源；找不到可信仓库的直接说「搜不到，大概率是编的名字」
④ 交付一张表：值得装 / 已有替代（写明用哪个顶）/ 搜不到
⑤ 只装真缺的（本次 19 个里只装了 4 个）
```

**近似替代清单（遇到就顶回去，不要重复装）**

| 榜上的名字 | 本地已有的 |
|:--|:--|
| Viral Writer / Viral_Writer_Skill | `viral-copywriter` |
| xiaohongshu-ops-skill | `xiaohongshu-content-ops`（自写，更贴业务） |
| html-anything | `baoyu-markdown-to-html` |
| GPT-Image2-Skill | `baoyu-image-gen` |
| guizang-ppt-skill | `frontend-slides` / `baoyu-slide-deck` |
| video-to-subtitle-summary | `video-pipeline` |
| WeChat-Official-Account-studio | `baoyu-post-to-wechat` / `gzh-design` |
| excalidraw-diagram | `excalidraw` |
| baoyu-skills（合集） | 已装 21 个 |

**必须说的一句实话**：榜单里「装上就能火」是假的。装更多工具不会让内容变好——
他的卡点是“发出去”，不是缺工具。**先装 1–2 个马上能用上的，并当场拿他真实业务跑一次案例**（见第九节）。

## 一、先定类型：skill / 应用 / CLI

**这一步错，后面全是白干。**

| 类型 | 判据 | 装法 |
|:--|:--|:--|
| **skill**（最常见） | 仓库里有 `SKILL.md` | 链接目录到 `~/.hermes/skills/` |
| **桌面应用** | 有 `.exe`/`.dmg` 安装包、Electron | 下载 + 校验 sha256 + 让用户点 UAC |
| **CLI 工具** | Rust/Go 单体二进制 | 下 release 包 → `~/.local/bin/` → `--version` 验证 |

**桌面应用装不了时不要硬试**：静默 `/S` 被 UAC 拦下就 `Start-Process` 弹出窗口，让用户点「是」。
我没有管理员权限，这一步必须他做——先说清楚再动手，别反复静默重试。

## 二、取包：`git clone` 会卡死，用 codeload tar

```bash
# ① 先试 git clone --depth 1：网络好时几个仓库几秒拉完（实测 3 个仓库 7 秒）
#    逐个套 `timeout 120`，别让一个仓库卡死整批
# ② clone 超时或 pack 阶段卡住 → 退 codeload tarball
curl -sL -m 120 -o /tmp/x.tgz \
  https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/main
#    分支可能是 master → 两个都试，10000 字节以下当失败
```

**⛔ 不要在同一个 `execute_code` 里对多个 URL 循环跑裸 `curl`**：长连接会被中断（orphan interrupt），
整批白跑且残留文件不知是否完整。要么每批 ≤3 个、要么改用 clone。

**只有单文件技能（只有 SKILL.md、没有配套脚本）**：不要软链，建目录再写文件
```bash
mkdir -p ~/.hermes/skills/<category>/<name>
# 把下载到的 SKILL.md 写进去（确认首行是 --- name: <name>）
```

解压用 Python `tarfile`（这台机器没有 `unzip`），解出一层 `<repo>-<branch>/` 再 `shutil.move` 到目标目录。

## 三、找仓库：GitHub Search API 按星排序

```bash
curl -s "https://api.github.com/search/repositories?q=<name>+in:name&sort=stars&order=desc&per_page=5"
```

- 榜单给的星数和仓库实时星数会差（涨了），**用 `full_name` 对，不要用星数对**
- 同名 fork 很多，认 star 最高的那个原始仓库

## 四、认结构：`SKILL.md` 的位置五花八门

```bash
find <repo> -name 'SKILL.md' -not -path '*/node_modules/*' | head -30
```

四种常见布局，链接的**目标层级完全不同**：

```
<repo>/SKILL.md                         → 链仓库根目录
<repo>/skills/<name>/SKILL.md           → 链每个子目录
<repo>/.agents/skills/<name>/SKILL.md   → 同上（Codex 习惯）
<repo>/plugins/<p>/skills/<name>/SKILL.md → 同上
```

**只能用目录软链，不能只链 SKILL.md 文件** —— 很多 skill 的脚本、模板、references 都在同级。

```bash
ln -sfn /home/clown_zy/projects/<repo> ~/.hermes/skills/<category>/<name>
```

分类目录按用途放：创意/设计 → `creative`，营销 → `marketing`，不加分类直接放 `~/.hermes/skills/` 根也行。

## 五、🔴 防炸索引：大合集只做一个入口

**每个 skill 的 name + description 都会常驻上下文。**
本次实测：装完 71 个小 skill 后总数到 374，光目录就要占掉可观的一段 context。

```
< 10 个        → 直接全链
10–30 个       → 全链可以，但要告诉用户“新增了 N 个，要不要精简”
> 50 个（如 111 个的设计技能库）
               → 只建 1 个索引 skill（写明仓库路径 + 分类表 + “按需只读一个”），
                 子技能不链，用的时候直接 read_file 那个目录
```

**索引 skill 的正文只放：仓库绝对路径 / INDEX 路径 / 分类与数量表 / “一次只读一个”的纪律。**
不复制子技能内容。

### 大合集比“索引 + 远程目录”更好的做法：折叠成 references

用户反驳“我们自己写的在我们的认知范围以内，吸引不了别人”时，别再讲道理，
**直接装，但用折叠法**——一个入口 + 全部内容落在 `references/`。

```
① copytree 整目录，而不是只拷 SKILL.md：
   ~/.hermes/skills/<cat>/<name>-knowledge-base/references/<topic>/SKILL.md
   每篇自带的 references/ 、scripts/ 、assets/ 必须一起过去——
   否则文内 “read references/mechanisms.md” 这类相对链接全断
② 目录名用 `父分类__子主题` 扁平化（如 `01-内容创作__title-writing`），
   避免中文目录名在 file_path 里嵌套太深
③ 主 SKILL.md 生成时从每篇的 frontmatter description 自动抽一排索引表
   （中文 + 截到 ~56 字 + 管道符换成全角，否则破表格）
④ 读完目测一下体积：245 个 skill 折叠成 2 个入口 = 783 个文件 / 5MB，索引用量几乎为零
```

**什么时候折叠、什么时候软链**

| 形态 | 做法 | 例 |
|:--|:--|:--|
| 功能型（要跑脚本、要当 skill 调用） | 目录软链进 skills 树 | `short-form-video-script` |
| 知识型（只查不跑、量大） | 折叠成一个 `-knowledge-base` 入口 + references | 139 篇小红书库 / 106 篇社媒库 |

**主 SKILL.md 必须写的一句**：「与自有技能冲突时，一律以自有技能为准」——
外来库只补方法论和视角，不覆盖本地口径（不写年龄、不堆数据、不伪装买家、话题带 `[话题]#`）。

**验证**：`skill_view(name, file_path='references/<topic>/SKILL.md')` 能返回内容，
再随便抽一篇它的二级文件（`references/<topic>/references/xxx.md`）验一下深链不断。

## 五·五、GitHub 大合集：按当前链路挑子集，装完必做体积盘点

一个仓库动辄 160+ 个 SKILL.md（按平台铺：ebay-*、tiktok-shop-*、shopify-*…）。
**全装进去就是自己把索引炸了，而且大半和当前业务无关。**

```
① 先数：find <repo> -maxdepth 2 -name SKILL.md | wc -l
② 按当前项目的环节名单筛（不是按兴趣）：本项目 14 关需要哪些就装哪些
   实测：162 个里只装了 16 个，加另一个仓库 12 个 = 28
③ 装前先看体积，别只看名字：
   wc -m <skill>/SKILL.md；ls <skill> | grep -c 'references\|scripts'
```

**空壳的典型长相：1000 字上下，全篇是 Capabilities / Install / Usage / "Built by X" 四段，
没有一条可执行步骤，Open 了也只会让你 npx 装它自己。**
真货是 8KB 以上、或自带 `references/` / `scripts/`。

实测对比（同批安装）：

| skill | 字数 | 判断 |
|:--|--:|:--|
| cross-border-ecommerce | 36,431 | ✅ 真货，带引用数据、落地成本公式、阶段规划 |
| competitive-pricing-strategy | 11,009 | ✅ 有方法论 |
| serp-content-teardown | 10,361 | ✅ 带脚本 |
| ebay-seo | **1,078** | ❌ 空壳 |
| ebay-product-research | **1,048** | ❌ 空壳 |

**装完必须打一张体积表给用户，并直说“N 个里只有 M 个有真内容”。**
报“装了 28 个”而不说质量分布，等于把维护负担包装成战果。

**一个大技能里往往只值得抽出几条**：36k 字的那个只贡献了一条落地成本公式和三个漏项，
那就把公式抄进自己的技能，而不是把整个技能当成答案。

## 六、重名冲突：先扫再链

```python
import glob, os
existing = {os.path.basename(os.path.dirname(p))
            for p in glob.glob("/home/clown_zy/.hermes/skills/**/SKILL.md", recursive=True)}
conflicts = [n for n in candidates if n in existing]
```

**同名 skill 在两个目录会互相遮蔽，`skill_view` 直接加载失败。**
处理顺序：
1. 先跳过重名的不链
2. 若新版本更好 → 把旧的 `mv <name> <name>.bak_<日期>`
3. **备份必须移出 skills 树**（`~/.hermes/skills_backup/`）—— 留在树里的 `.bak` 目录同样会被扫成 skill，污染索引

## 七、验证（不验证等于没装）

```
① skill_view(name) 能返回 SKILL.md       ← 必须，不能只看目录在不在
② CLI：<tool> --version 能跑
③ 应用：Get-ChildItem $env:LOCALAPPDATA\Programs 能看到，或进程能起来
④ 二进制下载：核对 sha256（GitHub API 的 assets[].digest）
```

**装完给用户一句实话**：装了几个、索引多了多少、哪些他其实用不上（他可以要求精简）。

## 七·五、RedSkill：小红书官方技能商店（940 个 skill）

小红书 2026 年上线的官方分发通道，比 GitHub 榜单靠谱——**有审核、有版本号、有作者**。

### 安装（一次性）

```bash
# ① 先下脚本看再跑，不要盲管（脚本很短，1200 字节，只做 下载→解压→exec install.sh）
curl -fsSL https://redskill.xiaohongshu.net/install.md    # 官方说明，含真实下载地址
# ② 跑安装器
curl -fsSL https://fe-video-qc.xhscdn.com/fe-platform-file/<id>.sh | bash
#    只装 CLI 不装默认 skill： ... | bash -s -- --cli-only
```

装完：`~/.local/bin/redskill`（Python CLI）+ `~/.redskill/`；CLI 六个子命令
`install / search / list / uninstall / upgrade / self-upgrade`。

### ⚠️ 五个必踩的坑

```
① **不带 --dir 时它装到当前工作目录**，不是 ~/.hermes/skills
   实测：在 <C盘>/tdout/... 下跑 install → 装进了 <C盘>/tdout/.../skills/<name>
   → 永远写成 `redskill install <id> --dir $HOME/.hermes/skills`，装完先确认落点再继续

② 在 $HOME 下直接 install 会报：
   “install_root 父级是系统根 (/home/<user>), 拒绝在根级单目录下安装”

③ 默认多造一层 skills/：装到 <dir>/skills/<name>，Hermes 不认这层
   → move 到 <dir>/<name>，删空目录（里面混有 .redskill-lock.json，一并移走）

④ 有些包内部又套一层，且**一层里可能含多个技能**：
   pkg/<inner>/SKILL.md              → 内容上提，把 pkg 换成 inner 的名字
   pkg/skills/a/SKILL.md + b/SKILL.md → **每个都各自提平成独立技能**，不要只拍一个

⑤ identifier 要用搜索结果里的**完整名**，短名直接 404：
   ✅ editorial-material-poster    ❌ editorialposter
   ✅ gathered-scenes-zine-skill   ✅ zine-composition-beauty
   已下架 / 永久删除会回 code=40400 / 41000 → 搜同类替代，别反复重试同一个名字
```

**装完统一体检（一次跑完，别逐个看）**
```bash
for n in <名单>; do [ -f ~/.hermes/skills/$n/SKILL.md ] && echo "OK  $n" || echo "--  $n"; done
```
找不到 SKILL.md 就是嵌套没拍平；这一步不过就不要向用户报"装好了"。

**一条能跑通的写法**
```bash
cd ~/.hermes/skills/content-creation
redskill install xhs-title           # → content-creation/skills/xhs-title
# 然后用 Python 把 skills/ 下所有目录 move 到上级，删空目录
```

### 已装的四个（小红书内容线）

| identifier | 用处 |
|:--|:--|
| `xhs-title` | 8 个标题模板 + 情绪叠加 + 字词推敲 |
| `xhs-baokuan-wenan` | 爆款文案：5 标题 + 3 秒开头 + SCQA + 话题组合 + 发布前 8 条检查 |
| `xhs-cover-title` | 封面文案与标题 |
| `xhs-visual-director-skill` | 3:4 图文结构 + 逐页视觉方案 + 生成提示词 |

### 已装的八个（海报／杂志封面线 · 全部铺在 ~/.hermes/skills 根下）

这批是用户从一个「爆款海报 Skill」视频里截来的，真实存在且都在商店里。
**它们默认是“海报思维”（重构图轻信息），不是小红书双列信息流封面**——用错场景会被否。

| identifier | 能干什么 | 边界 |
|:--|:--|:--|
| `banner-design` | 活动横幅、主视觉，多美术方向 | 不写真人文案 |
| `zine-composition-beauty` | 照片→杂志排版海报 | 偏杂志内页 |
| `editorial-material-poster` | 照片/截图/混合素材→高级编辑海报 | 同上 |
| `gathered-scenes-zine-skill` | 实景拼贴 3:5（**含两个技能，装完要各自拍平**） | 需图像模型出插画场 |
| `scene-distillation-zine-v1-3` | 照片煮馏成极简海报（原图不作图层） | 同上 |
| `mono-color` | 单色/双色油墨视觉 | 只做背景与辅助页 |
| `algorithmic-art` | p5.js 代码生成底图 | 同上 |

**已下架/删除的（当次装不上，不用再试）**：`photo-editorial`（41000 永久删除，用 `editorial-material-poster` 顶）、
`distillation-zine`（40400，用 `scene-distillation-zine-v1-3` 顶）。

⚠️ `gathered-scenes-zine-skill` 装下来是 `skills/scenes-gathered-zine-v1-3/` + `skills/scene-distillation-zine-v1-3/` 两层结构，
**两个都各自提平成根级技能**，只拍平一个另一个就成了死文件。

**与自有技能的关系**：自有 `moments-wholesale-posting` / `xiaohongshu-content-ops` 是**用户逐条纠正过的本地口径**，
RedSkill 上的是**通用方法论**。冲突时以自有为准；方法论可以补进来（例：`xhs-title` 的“字词推敲”
—普通词→有爆发力的词，可以接在“判断型标题”之后用）。

### ⚠️ 榜单上的英文名在商店里常常 404 —— 换领域词反查等价物

自媒体榜上的名字多是自造的英文（`srt-enhancer` / `video-to-shorts` / `color-assist` / `ffmpeg-skill`），
`redskill search` 直接搜**一个都搜不到**。这不等于没货。

```
❌ 搜完那 10 个名字就回「搜不到，是编的」然后收工
✅ 改用中文领域词再搜一轮：字幕 / 剪辑 / 剪映 / ffmpeg / 音频 / 调色 / 视频 / 排版
   实测：srt-enhancer   → 搜「字幕」→ cinemacc-subtitle（10KB + 带 scripts，真货）
        jianying-editor → 搜「剪映」→ food-video-cut-01 / 剪映实操助手
        一次 search 返回几十到上百条（「视频」= 820 条），只看前 10 条的标题+作者就够
```

- 报账时把「榜上名字」和「商店真实 identifier」**分两列写**，别让用户以为搜到的是同一个东西。
- 体积小不等于废纸：`.5KB` 也可能是一段**纯提示词型**的可执行剪辑指令（色调/运镜/字幕规则全在里面），
  先读完再判定，别用体积一把尺量到底。
- 榜单存在但装不上时，最值的动作往往是“拿它能用的那 1–2 条口径去重做一版”——
  而不是继续找更多 skill。

### ⚠️ RedSkill 上也有空壳：搜到先看体积再装

940 个不是 940 个都有货。**装之前先 `redskill search`，装之后先 `wc -c SKILL.md`**：

| SKILL.md 体积 | 判断 |
|:--|:--|
| **< 3KB** | 空壳。常见形态：只剩“能力地图/识别信号/工作流”几个表格互相套，没一条能落地 |
| 3–8KB | 单点子技能，可能有用（看它有没有 `references/` `scripts/`） |
| **> 8KB 或带 references/scripts** | 真内容，值得装 |

实测：`font-pairing-pro`（字体搭配顾问）只有 2.7KB，打开是“景/限/读”三字反复说，
`references/cheatsheet.md` 也只有三行——**这种名头大的直接告诉用户“空壳，别装”**。
同批 `typesetter`（12.8KB 带实际排版能力）就是真货。

**领域性判断**：中文字体这类问题，RedSkill 上没有值得装的——
真正值钱的是**字体文件 + 渲染参数**，不是“方法论”（一个表格就写完了）。
搜过 9 个关键词（字体/font/排版/设计/字体搭配/中文排版/字库/宋体/标题字）确认。
遇到“方法论型”需求先去 `chinese-font-library` 和自有脚本找，别在商店里淘。

## 七·六、带运行依赖的设计类仓库（Editable-Design 这类）

有些仓库的 skill 不是纯文档，跑起来要 Node 和浏览器。**目录软链要链到仓库内部的 skill 目录**，
不能拷出来——它的脚本靠 `../../tools` 这类相对路径找依赖。

```bash
# 仓库结构：<repo>/skills/<name>/SKILL.md + <repo>/tools/
ln -sfn ~/projects/<repo>/skills/<name> ~/.hermes/skills/creative/<name>
# 软链后 ../../tools 仍能解析，拷出来就断
```

**两个装完必做的修复**（否则渲染直接报「no Chromium-based browser found」）：

```bash
# ① 指向本机已有的 chrome-headless-shell，不要另装 Chrome
export EDITABLE_DESIGN_BROWSER=/home/clown_zy/.cache/hf_browser/chrome-headless-shell-linux64/chrome-headless-shell
# ② 装它的 puppeteer-core（走国内源，几秒）
cd <skill_dir> && npm ci --prefix scripts --registry=https://registry.npmmirror.com
```

先跑 `scripts/doctor.sh` 看它自己报缺什么，再按行的提示补——它的 doctor 输出就是清单。

**这类 skill 的调用顺序是固定的**，不要自己拼 HTML 再找工具：
`init-poster.sh <target>` → 写 `index.html` → `check-poster.sh` → `render-poster.sh` → `wire-editor.mjs`。
渲染完**必须回头读图逐行念字**（它自己在输出里也要求），DOM 检查看不出裁切和叠字。

## 八、踩过的坑

| 坑 | 现象 | 对策 |
|:--|:--|:--|
| `git clone` 卡死 | 300s 无输出，无 .git 目录 | 用 codeload tarball |
| `unzip` 不存在 | exit 127 | Python `tarfile` / `zipfile` |
| 静默安装被 UAC 拦 | 目录没生成、进程没有 | 改非静默启动，让用户点一次 |
| PowerShell `$_` 被 bash 吃掉 | `无法将“.ProcessName”识别为 cmdlet` | 把脚本写成 `.ps1` 文件再 `-File` 执行，不要在双引号里塞 `$_` |
| 英文/中文输出乱码 | UnicodeDecodeError / GBK 乱码 | 捕获 bytes，`.decode("utf-8","replace")` |
| 批量读多个 SKILL.md 的 description 时报 `UnicodeDecodeError: invalid continuation byte` | 个别仓库的 md 不是纯 UTF-8 | `subprocess.run(..., text=True)` 会崩；改 `text=False` 或自己 `open(f,'rb').read().decode('utf-8','ignore')` |
| 装完 skill 看不见 | 索引用的是启动时快照 | 新 skill 可能要下一轮才进索引，但 `skill_view` 当场就能用 |
| **批量展平嵌套目录把分类容器一起毁掉** | 循环里“找最深一层 SKILL.md 再上提”，分类目录（无自己的 SKILL.md）也命中；`mv 子目录 → rm -rf 容器 → mv 回来` 后，**每个容器只剩那一个子项，其余全没** | 判定容器/实体只看**目录自己**有没有内容文件；批量重构前先 `cp -a` 快照 + dry-run；**永远不要在一个循环里同时 mv 和 rm**。完整流程见 `safe-bulk-file-operations` |

## 九、装完就做案例

用户的规矩：**装好的立马做案例，看看到底有什么改变**。

- 视频类 skill → 跑一遍它自带的模板出片（如 video-shotcraft 的 Ink Press 36 秒样片），
  抽帧看一眼确认不是黑屏，再压缩到 3–5MB 发 QQ
- 图片/图表类 → 拿他真实业务内容（店铺、商品、行情）出一张真东西
- 只装不做案例 = 下次他会问“这个有什么用”，你说不出来
