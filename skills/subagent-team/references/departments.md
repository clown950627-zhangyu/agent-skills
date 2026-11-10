# 技能 → 部门 映射表

给用户的业务线分类，不是按技能库目录分。新增技能时归到下面某一栏；归不进去的，先问“这条业务线存在吗”，不存在就不要为它立部。

## 部门总表

| 部门 | 职责 | 对应角色 | 我验收什么 |
|:---|:---|:---|:---|
| 服装部 | 出图服务、棚拍、产品资料、小红书/朋友圈文案 | 图文官 + 文案官 | 服装颜色/花型/质感有没有变（用户底线）；文案有没有踩平台红线；有没有乱加数据 |
| 音乐视频部 | 歌词打磨、出曲提示词、MV、切片、发布 | 内容官 | 亲耳听（无静音段）+ 亲眼看（无黑屏）+ 时长 ≤30s + 字幕位置/字体对上 |
| 健康部 | 营养、运动、康复、文献、个人方案 | 健康顾问 | 有没有越界做医疗建议；国内外证据有没有分开；数字有没有出处 |
| 技术部 | App、打包、脚本、自动化、设备 | 代码官 | 自己跑一遍；`ls -lh` 看产物；有副作用要可验证句柄 |
| 情报部 | 搜索、文献、比价、投资数据 | 情报官 | 抽查两条原始来源；数字必须有出处；样本量够不够 |
| 视觉文档部 | 图表、海报、VI、PPT、Word/Excel/PDF/OCR | 设计官 + 文档官 | 打开读一遍（缺项/乱码/编号断没断/字号） |
| 增长变现部 | 选题、投放、数据复盘、定价 | 增长官 | 数据是真数值；平台规则是最新的 |

## 各栏技能清单

### 服装部
`ai-apparel-photoshoot` `apparel-ai-service-ops` `garment-product-documents` `moments-wholesale-posting` `xiaohongshu-content-ops` `viral-copywriter` `image-gen` `agnes-ai-multimodal` `image-stylization` `brand-visual-identity-system`

### 音乐视频部
`ai-song-album-production` `songwriting-and-ai-music` `heartmula` `audio-clip-delivery` `ffmpeg-audio-safe` `lyric-timing-alignment` `lyric-video-serif` `fast-lyric-mv` `douyin-lyric-video` `vinyl-player-mv` `video-cover-design` `media-output-sanity-check` `songsee` `douyin-music-promo` `short-video-music-distribution` `video-clipper` `video-pipeline` `videocut` `framewise-video-rendering` `douyin-video` `smart-short-video`

### 健康部
`health-lifestyle-business` `medical-literature-search`

### 技术部
`single-file-mobile-app` `android-webview-apk-packaging` `ai-app-development-methodology` `tech-animated-charts` `android-tv-launcher-custom` `used-mini-pc-build` `windows-operations` `lan-device-access` `hardware-concept-design` `html-to-pdf-poster-chrome` `hermes-agent` `computer-use` `subagent-team`

### 情报部
`multi-search-engine` `jina-reader` `url-content-loading` `url-readmode-markdown` `arxiv` `blogwatcher` `polymarket` `grounded-citations` `decision-advice-integrity` `stock-analysis` `stock-watcher` `yahoofi-info-signal` `china-equity-analysis` `market-environment-analysis` `financial-analysis` `dcf` `quantitative-methods` `baidu-ecommerce-search`

### 视觉文档部
`tech-animated-charts` `chart-visualization` `dashboard-creator` `architecture-diagram` `excalidraw` `drawio-skill` `baoyu-infographic` `baoyu-comic` `claude-design` `popular-web-designs` `design-md` `animation-gen` `p5js` `manim-video` `powerpoint` `docx` `chinese-word-documents` `xlsx` `excel-chinese-business-documents` `pdf` `nano-pdf` `ocr` `ocr-and-documents` `chinese-font-library`

### 增长变现部
`ai-content-monetization` `content-strategy` `social-content` `copywriting` `ai-seo` `seo-audit` `ai-media-production-pipeline` `visual-content-production` `ideation`

## 不进部门的（归档候选）

```
模型训练/推理（mlops 全目录）—— 除非要本地跑模型
游戏（gaming）、苹果生态（apple）、智能家居、红队（red-teaming）
技能市场本身（find-skills / skill-finder / skill-vetter）—— 管理工具，不算业务
```

不删，移入 `.archive/`，要用再取。

## 判断新需求属于哪个部门

```
“这个能不能卖”        → 增长变现部
“这个长什么样”        → 服装部（服装类）/ 视觉文档部（其他）
“这个对不对”          → 我本人（质检）
“这个能不能装上手机”  → 技术部
“这个数字哪来的”      → 情报部
“这个人该不该这么练”  → 健康部
```
