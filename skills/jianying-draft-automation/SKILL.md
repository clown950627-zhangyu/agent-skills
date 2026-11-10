---
name: jianying-draft-automation
description: 用剪映批量出营销短视频（草稿生成/改文案/导出）必读
---

# 剪映草稿自动化

让剪映批量出片、或按用户要求把片子做成「他能在剪映里自己改」的样子时读。
剪映没有公开 API，**官方自带的 `jianying-agent-cli.exe` 需要 `JIANYING_AGENT_RUNTIME_TOKEN`（内部令牌，拿不到）**，所有 `draft query-content/plan-patch/apply-patch` 都回 `PERMISSION_DENIED`。可行路线只有一条：**克隆一份能打开的草稿，改 JSON**。

## 目录与文件

```
剪映程序   %LOCALAPPDATA%\JianyingPro\Apps\<版本>\JianyingPro.exe
草稿目录   %LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft\<草稿名>\
  ├─ draft_content.json   时间轴/素材/文字（真正要改的）
  └─ draft_meta_info.json 草稿元信息（名字、路径、时长、id）
```

## 工作流

1. **先找一个剪映能正常打开的草稿当模板**（用户自己建的、或上一次成功生成的）。不要凭空写 JSON——字段太多，缺一个就打不开。
2. `cp -r` 整个草稿目录成新目录，只改里面的两个 JSON。
3. 改 `draft_content.json`：`tracks`（轨道）、`materials`（素材）、`duration`（总长，微秒）、`canvas_config`（竖屏写 `{"width":1080,"height":1920,"ratio":"9:16"}`）。
4. 改 `draft_meta_info.json`：`draft_id`（新 UUID 大写）、`draft_fold_path`（Windows 风格 `C:/...`）、`draft_name`、`draft_duration`。
5. **回剪映首页让它重扫草稿列表**，打开确认能显示时间轴，再谈导出。只写文件不打开＝没验证。

## JSON 结构要点（容易猜错的地方）

```
照片素材   materials.videos[]，type="photo"，path 用 C:/ 正斜杠，width/height 填真实像素
time range source_timerange / target_timerange 的 duration 单位是【微秒】（3 秒 = 3000000）
文字素材   materials.texts[]，content 是【JSON 字符串】，不是对象
            真实文案在 content 里解析出来的 text 字段
            字号 styles[0].size、粗体 styles[0].bold
            颜色 styles[0].fill.content.solid.color = [0~1 浮点 R,G,B]
文字位置   segment.clip.transform.y 是归一化值：0=画面中心，正数向下，负数向上
            底部字幕约 0.28~0.34；顶部标题约 -0.34
```

改完用 `json.load` → `json.dumps(ensure_ascii=False)` 落盘，别手拼字符串。

## 版式规矩（踩过的）

- **文字绝不遮人物脸。** 竖图人物居中时，字幕放画面下部 1/3（压在裤子/裙摆上可以），不要放上半身。
- **黑底不配白字。** 深色背景改米白 `#F1E9D8` / 沙色 `#D9C9A8`；ffmpeg 里写 `fontcolor=0xF1E9D8`，别用 `color=white`。
- **素材顺序按图逐个核对**，不要照抄别处建好的时间轴。图自带菜名/标题时，开图确认再配文案——错一张，整条片卖点和画面对不上。
- **字幕不重复图里已有的标题。** 图里有书法菜名，字幕就放卖点（慢炖四小时 / 炭火现烤）；重复等于噪音。
- **服装原图直接用，不许重绘。** 颜色/花型/面料一变就是废片，只允许换背景、调光、加字。
- 片长 10–13 秒、每张 2.5–3 秒最适合竖屏信息流；一张 3 秒、四张 12 秒是安全基线。

## 原图自带水印怎么处理

素材常带「FORM-01 | 弧侧空间 / 概念效果图|非生产技术图」这类角标，对外发布必须去掉。

```
❌ 顶部整条 boxblur —— 会把人脸一起糊掉，废片
✅ 只盖水印 bbox：split → crop=<水印宽>x<水印高>:0:0 → boxblur=22:3 → overlay=0:0
   水印在纯色背景上时，模糊后几乎看不出来；确认 bbox 右手边不进人脸
✅ 横向裁切：图够宽时从水印那侧裁掉（crop=1080:1920:iw-1080:0 取最大左裁）
```

先量一下水印在原图的像素范围再决定用哪种，别凭感觉。

## 横图做竖屏：不要硬裁

4:3 的菜品图硬裁成 9:16 会把图里自带的菜名切成半个字。改用毛玻璃垫底：

```
背景  scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.24
前景  scale=1080:-2（等比缩到宽 1080），居中 overlay
文字  放在虚化区（下部），不压菜品
```

**但主体是建筑/招牌/夜景这类整幅画面时，毛玻璃是错的**：上下虚化区会压成两条死黑带，
中间一块小图，整体失重（夜景图的虚化里还会飘出一个巨大的虚灯笼）。判据是「这张图有没有
单一主体值得保住比例」：有（菜品、人像）→ 毛玻璃；没有（门头、街景、星空）→ **直接满屏
裁切 `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920` + 慢推镜**，
两侧被切掉的边缘信息通常不值钱。

## 含音频的草稿：最小结构可以直接写（已实测剪映接受）

写 `materials.audios[]` 一条 + 一条 `type:"audio"` 轨道，剪映打开时**照单全收**，
并把它重写进 `Timelines/<UUID>/draft_content.json`。**文件被剪映改写＝解析成功**，这就是最硬的验证，
不用等导出。

```
前提①  素材路径用 C:/ 正斜杠；wav / mp3 都行
前提②  只有「没被打开过的明文草稿」能写；已打开过的顶层 draft_content.json 是二进制，碰不得
```

候选模板是 0 字节或半截 JSON（别人写一半被叫停）→ 跳过即可，它当不了模板，但**不妨碍你自己写**。

交付前必核：`ffprobe` 有 audio 流 + `-af volumedetect` 不是静音（mean_volume 有值）。

## 驱动剪映窗口（只能做最后确认）

草稿能不能打开，**先读 `draft_content.json` 验结构，再开窗口看一眼**；不要靠点击去"操作"剪映。

- 会话分辨率会变（1024×768 与 1920×1080 都见过），菜单项坐标随之全变；`SetProcessDPIAware()` 只解决 DPI，不解决分辨率变化。
- **第一次点击只激活窗口，不触发控件**：同一位置要点第二次。QQ 消息提示会抢焦点，
  自动化期间每轮操作前先把窗口重新置前（`SetForegroundWindow`），否则点击全落空、看起来像"点了没反应"。
- 左侧 tab（素材/音频/文本/贴纸/特效/转场…）在 1024 宽下挤在一起，点偏一格就停在素材面板不动。
  **每轮先截图放大，读出各 tab 中心 x 再用**，不要凭上一轮记下的坐标。
- 草稿格子顺序随修改时间重排，刚新建的草稿可能插在中间；**先截图认格子再双击**，别沿用旧坐标。
- 菜单项顺序会随编辑页/首页不同，点错会弹「全局设置」这类模态框，之后所有点击都进不去。
- 登录态/会员到期日这类事实**读面板比读按钮文案准**：右上角「现在开通」广告位 SVIP 也显示。

### 要只开自己的新草稿：把旧草稿移出草稿目录

格子顺序不可靠、又点错过草稿时，别在格子上猜：

```
① 关掉剪映
② mv 旧的草稿目录 → com.lveditor.draft 之外的 _backup_drafts/（不是删）
③ 重开剪映 → 首页只剩新草稿，第一格就是它
④ 剪映可能弹「草稿列表异常 检测到部分草稿丢失」→ 点「取消」，不要点恢复
```

### 特效 tab 点不动时，不要在上面耗

左侧 tab 点击不生效（面板一直停在「素材」）时，换三次坐标还不行就停手。
原因：草稿里加特效需要剪映内部资源 ID（`materials.effects[]` + effect 轨道），
没法凭空写；界面点不进去就加不上。

```
✅ 先问用户要哪种特效（光感/胶片颗粒/转场/描边字），并在交付时写明「特效未加，位置已留」
❌ 连点十几下同一个 tab 假装在做，然后发一个没特效的片当完成
```

### PowerShell 脚本里的中文会静默失效

`.ps1` 写 UTF-8（无 BOM）时，Windows PowerShell 5.1 按 ANSI 读，中文路径/中文文件名变成乱码，
报 `PathNotFound` 而不是编码错误——看起来像目录不存在。

```
❌ Get-ChildItem 'C:\Users\用户\AppData\Local'      → PathNotFound
✅ 用环境变量：$env:LOCALAPPDATA / $env:USERPROFILE
✅ 中文文件名用码点拼：$n = [char]0x526A + [char]0x6620   （剪映 = 剪+映）
✅ 输出重定向到 UTF8 文件再 read_file 读，别让 PowerShell 控制台用 GBK 吐回给 bash
```

## 登录态判别

编辑页右上角「现在开通，低至 X 元/天」是**广告位，SVIP 登录着也照样显示**——不能据此判断未登录。

```
菜单 → 账号：出现「永久注销账号」＝ 已登录（未登录会显示「登录」）
要看会员到期日：点右上角那条广告，会员面板显示昵称、SVIP 到期日、云空间、积分
```

会员等级影响导出水印和 AI 功能权限，交付前确认一次。

## 11.7 版草稿会搬家并加密（2026-11-08 实测）

剪映 11.7 一旦**打开过**某个草稿，会把时间轴迁到
`<草稿>/Timelines/<UUID>/draft_content.json`，顶层 `draft_content.json` 可能变成
base64 二进制（解出来是压缩/加密数据，不是明文 JSON）。

```
✅ 可写：没被剪映打开过的草稿（pure 明文 JSON），剪映打开时会照单全收
❌ 别写：已打开过的草稿顶层文件（二进制，改了必打不开）
✅ 能改：打开后生成的 Timelines/<UUID>/draft_content.json —— 这份仍是明文
```

所以流程是：写完 → 打开验证 → 之后只改 `Timelines/*/draft_content.json`。

## 多时间线：克隆模板必删 Timelines/

从有 `Timelines/` 的模板 `cp -r` 出来，剪映会显示「时间线01 + 时间线02」（旧内容占着一条）。
修法（先关掉剪映）：

```
① <草稿>/Timelines/project.json  设 main_timeline_id = 保留的 UUID，timelines 只留这一条
② 删掉 Timelines/<旧UUID>/
③ 保留那条的 draft_content.json 里确认 videos / audios / texts 都在
```

## 音频素材：最小可用结构（已验证剪映认）

`materials.audios[]` one entry 就够，缺的字段留空字符串：

```json
{"id": "<大写UUID>", "type": "extract_music", "path": "C:/.../x.wav",
 "name": "x.wav", "material_name": "x.wav", "duration": 32000000,
 "category_name": "local", "music_id": "", "source_platform": 0, "app_id": 0,
 "check_flag": 1, "is_ai_clone_tone": false, "is_query": 0, "is_ugc": 0,
 "material_id": "<同上>", "orgtark_duration": 32000000, "wave_points": []}
```

轨道用 `type:"audio"`，segment 的 `target_timerange.start` 控制音乐何时进入，
`extra_material_refs` 可直接复用视频轨段的引用列表。

## 竖版画布放横图：先问清「能不能裁」

```
用户说「保持原来的图」「别缩放」＝ 一个像素都不许裁。此时用双视频轨：
  轨1 底层 模糊底：同图 scale 放大 + crop 1080x1920 + gblur=sigma=42 + 压暗
  轨2 上层 原图  ：clip.scale 设 1.0，剪映按 contain 居中，完整不裁
  两条轨时长 = 主时间轴时长，render_index 递增（0 底 / 1 上）

用户不介意裁、主体又居中 → 单轨满屏 crop，画面更满更沉浸
```

**自己先裁了再交，大概率被打回**：裁切改构图，招牌边角被切掉用户一眼就看出来。
默认给「不裁」的垫底版，要满屏再问一句。

`clip.scale` 设 1.0 是 **contain 不是 cover** —— 竖版画布塞横图必然上下留黑边，不会自动铺满。
导出后必抽帧看黑边，别等用户发现。

## 导出（界面路径）

```
右上「导出」→ 对话框（标题/位置/分辨率/帧率）→ 右下角「导出」
默认落 %USERPROFILE%\Videos\<标题>.mp4，重名自动加 (1)
37 秒 1080×1920 约 55MB，发 QQ 前用 crf 25 + maxrate 2.6M 压到 ~2MB
```

## 用户说「用剪映做」是什么意思

不是「给我一个 mp4」也不是「给我一个草稿」，是：**成片能用上剪映那套手段——特效、字体、字幕样式**。

```
✅ 素材进草稿 + 音频 + 字幕 + 特效/转场 + 在剪映里导出
❌ 只把图/音塞进草稿（他会问「你在用剪映吗」）
❌ ffmpeg 渲完再附一个草稿交差（他会问「特效怎么没用上去」）
```

**特效与字体是交付的一部分，不是可选项。** 交付前先确认要哪些（光感/胶片颗粒/转场/描边字），
确认不了的就在草稿里留出位置并**明确告诉用户「特效我没加」**——不要让他自己发现。

## 和 ffmpeg 的分工

剪映能做的（切图、字幕、模板、导出）交给剪映；**需要精确运镜（缓推镜）、交叉淡化、批量统一字体排版时用 ffmpeg 渲染成片**，同时仍然生成一份剪映草稿——用户要的是「客户改一句文案我两分钟能改完」，草稿的价值就在这里。

具体镜头链、调色参数、结尾卡和拼接公式见 `references/ffmpeg-vertical-promo.md`。

**ffmpeg 返回 0 不代表滤镜生效**：chain 没真正接进 `-filter_complex` 时，它会把源图原样编码输出，rc 照样 0、文件照样能播。**每次渲染后 `ffprobe` 核 width/height 是否为 1080×1920**，再抽帧读一遍文字，才算验过（`media-output-sanity-check` 那套）。
