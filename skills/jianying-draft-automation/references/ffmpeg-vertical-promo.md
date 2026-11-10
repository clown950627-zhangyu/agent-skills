# 竖屏营销片 ffmpeg 渲染配方

图片轮播型（4–6 张图 → 10–13 秒 1080×1920）用这套。要做「运镜 + 转场 + 统一排版」就只能走 ffmpeg，剪映草稿同时留一份给用户自己改。

## 单张镜头链

竖图（3:4 人像）：

```
scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
zoompan=z='min(zoom+0.00055,1.10)':d=<帧数+2>:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,
eq=brightness=-0.02:saturation=1.05,
drawtext=...
```

横图（4:3 菜品）：毛玻璃垫底，**不要硬裁**，硬裁会把图里自带的书法标题切成半个字。

```
[0:v]split[o1][o2];
[o2]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.24[bg];
[o1]scale=1080:-2[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2[sc];
[sc]<zoompan>,<调色>,<drawtext>[v]
```
前景务必 `overlay` 在**垂直居中**（`(H-h)/2`）。放到顶部（如 `y=210`）会让下半屏空一大片，看着像没做完。

## 拼接

```
total = n*dur - (n-1)*xfade_dur          # 例 5×2.6 - 4×0.18 = 12.28s
offset 累加：off += dur - xfade_dur
transition  缓和人像用 fade，餐饮/节奏感用 fadeblack
```

## 调色配方

食物（暖黄柔光、低饱和、有食欲）：

```
eq=brightness=0.015:saturation=0.93:contrast=1.04,
colorbalance=rm=0.06:gm=0.02:bm=-0.06:rh=0.04:bh=-0.04
```

人像（保持面料本色，只轻微提饱和，**不许变色**）：

```
eq=brightness=-0.02:saturation=1.05
```

## 结尾卡（品牌 + 地址）

深棕底 `0x2A1F18` + 米白字 `0xF1E9D8` / 沙色 `0xD9C9A8` + 一条细砖红横线。不要黑底白字。

```
color=c=0x2A1F18:s=1080x1920:d=<dur>:r=30,
drawtext=...fontsize=104:y=830,        # 主名（衬线 NotoSerifSC-VF）
drawbox=x=460:y=952:w=160:h=3:color=0xA33B2C@0.9:t=fill,
drawtext=...fontsize=54:y=1000,        # 地址
drawtext=...fontsize=40:y=1096         # 营业信息
```

竖排居中的三行，纵向中心落在画面 43%–57% 之间；整体偏上会显得下坠。

## 坑（每个都实际踩过）

1. **`rc=0` 不等于滤镜生效。** 把 chain 拼在变量里却没真正接进 `-filter_complex` 时，ffmpeg 会原样把源图编码输出，退出码照样是 0，文件也是有效 mp4。**每次渲染后必须 `ffprobe -show_entries stream=width,height` 核 1080×1920**，不能只看返回码。
2. **滤镜链里 `[0:v]` 只能用一次。** 要用两遍（垫底 + 前景）必须先 `split`，否则报错。
3. **顶部整条 boxblur 会连人脸一起糊掉。** 只模糊水印 bbox（`crop=<宽>x<高>:0:0,boxblur=22:3`），先量 bbox 再定尺寸，右手边不能进人脸；背景是纯色时模糊后几乎看不出来。
4. **`crop=1080:1920:iw-1080:0` 取最大左裁能去掉水印，但会把模特手臂切掉。** 宁可走 bbox 模糊。
5. **素材顺序按图核对，不要照抄别处的时间轴。** 图自带菜名/标题时，逐个开图确认再配文案；错一张，整条片的卖点和画面对不上。
6. **字幕别重复图里已有的标题。** 图里已有书法菜名，字幕就放卖点（慢炖四小时 / 炭火现烤），重复＝噪音。
7. **drawtext 中文一律 `textfile=` 传文件**，别把中文塞进命令行参数，转义和编码两头都会炸。

## 自检（交付前跑）

```
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 out.mp4
  期望 1080,1920,<10–13s>
抽帧看字：-ss <中间时刻> -frames:v 1 /tmp/x.png，然后自己读一眼
  看三件事：是否黑屏、中文有没有方块、文字有没有压人脸/压标题
```
