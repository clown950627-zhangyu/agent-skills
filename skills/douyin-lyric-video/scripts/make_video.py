#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《且听风来》v3：主歌段（不用副歌）+ 加强结尾帧"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/path/to/project"
IMGS = f"{ROOT}/画面_广角"
SONG = "/path/to/project"
CN_FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
CN_BOLD = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
EN_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
W, H = 720, 1280
INTRO_D = 1.0
AUDIO_START = 58.8
AUDIO_LEN = 31.7
DELAY_MS = 300
END_D = 4.0            # 结尾帧4秒·静态·渐黑
BODY = AUDIO_LEN
OFFSET = AUDIO_START - DELAY_MS/1000.0

def dt(d, text, y, font, spacing, color, alpha):
    ws = [font.getbbox(c)[2]-font.getbbox(c)[0] for c in text]
    total = sum(ws)+spacing*(len(text)-1); x = (W-total)//2
    for c, w in zip(text, ws):
        bb = font.getbbox(c); d.text((x-bb[0], y), c, font=font, fill=color+(alpha,)); x += w+spacing

def make_intro(img_path, out):
    bg = Image.open(img_path).convert("RGB").resize((W,H))
    bg = Image.eval(bg, lambda x: int(x*0.55))
    img = bg.convert("RGBA")
    sh = Image.new("RGBA", (W,H), (0,0,0,0)); sd = ImageDraw.Draw(sh)
    f1 = ImageFont.truetype(CN_BOLD, 76); f2 = ImageFont.truetype(CN_FONT, 26); f3 = ImageFont.truetype(CN_FONT, 20)
    dt(sd, "且听风来", int(H*0.36)+3, f1, 16, (0,0,0), 220)
    dt(sd, "专辑 · 人生慢", int(H*0.36)+128, f2, 5, (0,0,0), 190)
    dt(sd, "作词 作曲 编曲 演唱 · 楼上用户", int(H*0.36)+178, f3, 3, (0,0,0), 170)
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    dt(d, "且听风来", int(H*0.36), f1, 16, (255,252,246), 255)
    d.line([(W//2-90, int(H*0.36)+106), (W//2+90, int(H*0.36)+106)], fill=(235,224,205,190), width=2)
    dt(d, "专辑 · 人生慢", int(H*0.36)+128, f2, 5, (235,226,211), 245)
    dt(d, "作词 作曲 编曲 演唱 · 楼上用户", int(H*0.36)+178, f3, 3, (215,206,192), 225)
    img.convert("RGB").save(out, quality=95)

def render_sub(cn, en, out):
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    fs_cn = 42 if len(cn) <= 13 else 34
    f_cn = ImageFont.truetype(CN_FONT, fs_cn)
    f_en = ImageFont.truetype(EN_FONT, 15)
    cs, es = 4, 1
    ws = [f_cn.getbbox(c)[2]-f_cn.getbbox(c)[0] for c in cn]
    tw = sum(ws)+cs*(len(cn)-1); x0 = (W-tw)//2
    y0 = int(H*0.50) - fs_cn//2
    ews = [f_en.getbbox(c)[2]-f_en.getbbox(c)[0] for c in en]
    etw = sum(ews)+es*(len(en)-1); ex0 = (W-etw)//2
    ey0 = y0 + fs_cn + 16
    glow = Image.new("RGBA", (W,H), (0,0,0,0)); gd = ImageDraw.Draw(glow)
    x = x0
    for c, w in zip(cn, ws):
        bb = f_cn.getbbox(c); gd.text((x-bb[0], y0), c, font=f_cn, fill=(0,0,0,100)); x += w+cs
    x = ex0
    for c, w in zip(en, ews):
        bb = f_en.getbbox(c); gd.text((x-bb[0], ey0), c, font=f_en, fill=(0,0,0,80)); x += w+es
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(img)
    x = x0
    for c, w in zip(cn, ws):
        bb = f_cn.getbbox(c); d.text((x-bb[0], y0), c, font=f_cn, fill=(255,255,255,228)); x += w+cs
    x = ex0
    for c, w in zip(en, ews):
        bb = f_en.getbbox(c); d.text((x-bb[0], ey0), c, font=f_en, fill=(245,245,245,208)); x += w+es
    img.save(out)

SEG = f"{ROOT}/片段3"; os.makedirs(SEG, exist_ok=True)
SUBD = f"{ROOT}/字幕3"; os.makedirs(SUBD, exist_ok=True)
STRIPD = f"{ROOT}/字幕条3"; os.makedirs(STRIPD, exist_ok=True)

names = ["w1_海岸线","w2_花海","w3_山河","w4_月下大地","w5_归途","w6_辽阔"]
make_intro(f"{IMGS}/{names[0]}.jpg", f"{ROOT}/片头卡3.jpg")
intro = f"{ROOT}/片头3.mp4"
subprocess.run(["ffmpeg","-y","-v","error","-loop","1","-t",str(INTRO_D),"-i",f"{ROOT}/片头卡3.jpg",
    "-vf","fade=t=in:st=0:d=0.3,fade=t=out:st=0.6:d=0.4,scale=720:1280,format=yuv420p",
    "-r","25","-c:v","libx264","-crf","19","-pix_fmt","yuv420p",intro],capture_output=True)

dur = BODY/6
segs = [intro]
for i, nm in enumerate(names):
    out = f"{SEG}/v{i}.mp4"
    frames = int(dur*25)
    mode = i % 3
    if mode == 0: z = "min(1+0.0007*on,1.10)"; xy = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    elif mode == 1: z = "if(eq(on,0),1.10,max(1.10-0.0007*on,1.0))"; xy = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    else: z = "1.06"; xy = "x='iw/2-(iw/zoom/2)+on*0.6':y='ih/2-(ih/zoom/2)'"
    vf = (f"scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
          f"zoompan=z='{z}':d={frames}:{xy}:s={W}x{H}:fps=25,"
          f"eq=saturation=1.0:contrast=1.04,noise=alls=3:allf=t+u,vignette=PI/7,format=yuv420p")
    subprocess.run(["ffmpeg","-y","-v","error","-i",f"{IMGS}/{nm}.jpg","-vf",vf,"-frames:v",str(frames),
                    "-c:v","libx264","-crf","19","-preset","veryfast","-pix_fmt","yuv420p",out],capture_output=True)
    segs.append(out)

# ===== 加强结尾帧（3秒·明确可见）=====
endcard = f"{ROOT}/结尾帧3.jpg"
bg = Image.open(f"{IMGS}/{names[-1]}.jpg").convert("RGB").resize((W,H))
bg = Image.eval(bg, lambda x: int(x*0.38))     # 更暗·让字更清楚
img = bg.convert("RGBA")
d = ImageDraw.Draw(img)
dt(d, "且听风来", int(H*0.40), ImageFont.truetype(CN_FONT, 52), 12, (252,249,242), 240)
d.line([(W//2-100, int(H*0.40)+92), (W//2+100, int(H*0.40)+92)], fill=(220,208,190,200), width=2)
dt(d, "慢慢走", int(H*0.40)+130, ImageFont.truetype(CN_FONT, 46), 8, (252,249,242), 245)
dt(d, "不必慌张", int(H*0.40)+212, ImageFont.truetype(CN_FONT, 46), 8, (252,249,242), 245)
img.convert("RGB").save(endcard, quality=95)
end_v = f"{ROOT}/结尾帧3.mp4"
subprocess.run(["ffmpeg","-y","-v","error","-loop","1","-i",endcard,
    "-vf",f"scale={W}:{H},fade=t=in:st=0:d=0.6,fade=t=out:st={END_D-1.2}:d=1.2:color=black,format=yuv420p",
    "-frames:v",str(int(END_D*25)),"-c:v","libx264","-crf","19","-pix_fmt","yuv420p",end_v],capture_output=True)
segs.append(end_v)

lf = f"{SEG}/list.txt"
with open(lf,"w") as f:
    for s in segs: f.write("file '" + os.path.abspath(s) + "'\n")
joined = f"{ROOT}/拼接3.mp4"
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",lf,"-c","copy",joined],capture_output=True)
jd = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",joined],capture_output=True,text=True).stdout.strip() or 0)
print(f"拼接: {jd:.2f}s")

# ===== 主歌段字幕（精确时间）=====
LYRICS = [
    (59.16, 62.38, "且听风来 且看花开", "hear the wind come, watch the flowers bloom"),
    (62.38, 65.78, "且把昨日的故事放下来", "let yesterday's stories go"),
    (66.40, 68.24, "这一生山高水长", "a lifetime of mountains and rivers"),
    (68.24, 70.06, "总有一处月光", "there is always moonlight"),
    (70.06, 73.06, "会照亮你回家的路上", "it will light the road home"),
    (73.64, 76.94, "且听风来 且等云开", "hear the wind come, wait for clouds to part"),
    (76.94, 80.34, "所有遗憾都会有安排", "every regret will find its place"),
    (80.92, 83.70, "若人生不过一场来往", "if life is just a passing through"),
    (84.26, 86.58, "就把温柔留在心上", "then keep the tenderness in your heart"),
    (86.58, 89.52, "慢慢走 不必慌张", "walk slowly, no need to hurry"),
]
timings = [(st - OFFSET, en - OFFSET) for st, en, _, _ in LYRICS]
print("字幕时间:", [(round(a,2), round(b,2)) for a,b in timings])
for i, (st, en, cn, en_txt) in enumerate(LYRICS):
    render_sub(cn, en_txt, f"{SUBD}/s{i}.png")
    Image.open(f"{SUBD}/s{i}.png").crop((0,560,W,760)).save(f"{STRIPD}/s{i}.png")

inputs = ["-i", joined]
for i in range(len(LYRICS)): inputs += ["-loop","1","-t",f"{jd:.2f}","-i", f"{STRIPD}/s{i}.png"]
fc = []; prev = "0:v"
for i, (st, en) in enumerate(timings):
    st_i = INTRO_D + st; en_i = INTRO_D + en
    fade = 0.4
    fc.append(f"[{i+1}:v]format=rgba,fade=t=in:st={st_i:.2f}:d={fade}:alpha=1,fade=t=out:st={max(st_i,en_i-fade):.2f}:d={fade}:alpha=1[s{i}]")
    outl = f"v{i}" if i<len(LYRICS)-1 else "vfin"
    fc.append(f"[{prev}][s{i}]overlay=0:560:format=auto:shortest=1[{outl}]")
    prev = outl
with_subs = f"{ROOT}/带字幕3.mp4"
r = subprocess.run(["ffmpeg","-y","-v","error"]+inputs+["-filter_complex",";".join(fc),
    "-map","[vfin]","-t",f"{jd:.2f}","-c:v","libx264","-crf","20","-preset","ultrafast",
    "-pix_fmt","yuv420p","-threads","3",with_subs],capture_output=True,text=True)
print(f"overlay {r.returncode}")

out_final = f"{ROOT}/且听风来_副歌完整_抖音版_v2.mp4"
fade_start = DELAY_MS/1000 + AUDIO_LEN - 1.5
r2 = subprocess.run(["ffmpeg","-y","-v","error","-i",with_subs,
    "-ss",str(AUDIO_START),"-t",str(AUDIO_LEN),"-i",SONG,
    "-filter_complex",f"[1:a]adelay={DELAY_MS}|{DELAY_MS},afade=t=in:st=0.3:d=0.3,afade=t=out:st={fade_start:.2f}:d=1.5,apad[a]",
    "-map","0:v","-map","[a]","-shortest","-c:v","copy","-c:a","aac","-b:a","192k",out_final],
    capture_output=True,text=True)
if os.path.exists(out_final):
    info = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration,size","-of","default=noprint_wrappers=1",out_final],capture_output=True,text=True).stdout.strip()
    print(f"🎬 {out_final} | {info}")
else:
    print("❌", r2.stderr[-200:])
