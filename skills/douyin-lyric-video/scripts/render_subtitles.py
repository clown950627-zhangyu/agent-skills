#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《三十岁的月亮》· 对齐参考风格（细衬线+无衬线英文+居中偏上+无暗底+柔光）"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/path/to/project"
SUBDIR = f"{BASE}/字幕_参考风格"
STRIP = f"{BASE}/字幕条_参考风格"
os.makedirs(SUBDIR, exist_ok=True); os.makedirs(STRIP, exist_ok=True)
CN_FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"   # 细衬线·不加粗
EN_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"           # 无衬线
W, H = 720, 1280

# 字幕（中英对照·英文小写）
SUBS = [
    ("三十岁的月亮 还挂在路上", "the moon of thirty is still on its way"),
    ("不怕它晚 就怕自己先慌", "i fear not its lateness but my own panic"),
    ("别人十五就圆 我十七才亮", "theirs full at fifteen mine at seventeen"),
    ("晚一点圆满 也一样有光", "a later fullness still gives light"),
    ("你的月亮 几号圆", "when will your moon be full"),
]

def render(cn, en, out):
    """参考风格：细衬线中文+无衬线小写英文·居中偏上(0.50H)·无暗底·纯白+柔光"""
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    fs_cn = 44 if len(cn) <= 13 else 40
    fs_en = 16
    f_cn = ImageFont.truetype(CN_FONT, fs_cn)
    f_en = ImageFont.truetype(EN_FONT, fs_en)
    cs, es = 4, 1
    ws = [f_cn.getbbox(ch)[2]-f_cn.getbbox(ch)[0] for ch in cn]
    tw = sum(ws)+cs*(len(cn)-1)
    x0 = (W-tw)//2
    y0 = int(H*0.50) - fs_cn//2          # 垂直居中
    ews = [f_en.getbbox(ch)[2]-f_en.getbbox(ch)[0] for ch in en]
    etw = sum(ews)+es*(len(en)-1)
    ex0 = (W-etw)//2
    ey0 = y0 + fs_cn + 16
    # 柔光晕染（大模糊·低透明·替代描边）
    glow = Image.new("RGBA", (W,H), (0,0,0,0)); gd = ImageDraw.Draw(glow)
    x = x0
    for ch, w in zip(cn, ws):
        bb = f_cn.getbbox(ch); gd.text((x-bb[0], y0), ch, font=f_cn, fill=(0,0,0,90)); x += w+cs
    x = ex0
    for ch, w in zip(en, ews):
        bb = f_en.getbbox(ch); gd.text((x-bb[0], ey0), ch, font=f_en, fill=(0,0,0,70)); x += w+es
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(9)))
    # 文字（纯白·85-90%透明·无描边）
    d = ImageDraw.Draw(img)
    x = x0
    for ch, w in zip(cn, ws):
        bb = f_cn.getbbox(ch); d.text((x-bb[0], y0), ch, font=f_cn, fill=(255,255,255,222)); x += w+cs
    x = ex0
    for ch, w in zip(en, ews):
        bb = f_en.getbbox(ch); d.text((x-bb[0], ey0), ch, font=f_en, fill=(245,245,245,205)); x += w+es
    img.save(out)

for i, (cn, en) in enumerate(SUBS):
    render(cn, en, f"{SUBDIR}/s{i}.png")
print(f"✅ 参考风格字幕 {len(SUBS)}屏")

# 条状裁剪（字幕在0.50H附近·裁y=560~760）
for i in range(5):
    im = Image.open(f"{SUBDIR}/s{i}.png")
    im.crop((0, 560, W, 760)).save(f"{STRIP}/s{i}.png")
print("✅ 字幕条")

# overlay（加-t限制！）
joined = f"{BASE}/拼接_带片头.mp4"
jd = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
    "-of","default=noprint_wrappers=1:nokey=1",joined],capture_output=True,text=True).stdout.strip() or 0)
OFF = 2.5
S = [(0.0+OFF,0),(5.5+OFF,1),(12.4+OFF,2),(17.6+OFF,3),(21.0+OFF,4)]
inputs = ["-i", joined]
for _, idx in S: inputs += ["-loop","1","-t",f"{jd:.2f}","-i", f"{STRIP}/s{idx}.png"]
fc = []; prev = "0:v"
for i,(st,idx) in enumerate(S):
    en = S[i+1][0]-0.3 if i+1<len(S) else jd
    fade = 0.5
    fc.append(f"[{i+1}:v]format=rgba,fade=t=in:st={st}:d={fade}:alpha=1,"
              f"fade=t=out:st={max(st,en-fade):.2f}:d={fade}:alpha=1[s{i}]")
    outl = f"v{i}" if i<len(S)-1 else "vfin"
    fc.append(f"[{prev}][s{i}]overlay=0:560:format=auto:shortest=1[{outl}]")
    prev = outl
with_subs = f"{BASE}/带字幕_参考风格.mp4"
r = subprocess.run(["ffmpeg","-y","-v","error"]+inputs+["-filter_complex",";".join(fc),
    "-map","[vfin]","-t",f"{jd:.2f}","-c:v","libx264","-crf","20","-preset","ultrafast",
    "-pix_fmt","yuv420p","-threads","3",with_subs],capture_output=True,text=True)
print("overlay:", r.returncode, f"{os.path.getsize(with_subs)//1024}KB" if os.path.exists(with_subs) else r.stderr[-150:])

out_final = f"{BASE}/三十岁的月亮_副歌_参考风格.mp4"
r2 = subprocess.run(["ffmpeg","-y","-v","error","-i",with_subs,
    "-ss","50","-t","22.5","-i",f"{BASE}/三十岁的月亮_Suno版.mp3",
    "-filter_complex","[1:a]adelay=2500|2500,afade=t=in:st=2.5:d=0.4,afade=t=out:st=21.5:d=1.2,apad[a]",
    "-map","0:v","-map","[a]","-shortest","-c:v","copy","-c:a","aac","-b:a","192k",out_final],
    capture_output=True,text=True)
if os.path.exists(out_final):
    info = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration,size",
        "-of","default=noprint_wrappers=1",out_final],capture_output=True,text=True).stdout.strip()
    print(f"🎬 {out_final} | {info}")
else:
    print("❌:", r2.stderr[-200:])
