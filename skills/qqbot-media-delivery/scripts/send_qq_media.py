#!/usr/bin/env python3
"""给它处脚本/定时任务直接调用的 QQ 发图·发文件·发文字工具（不依赖 agent 上下文）

用法：
    python3 send_qq_media.py --text "文字"
    python3 send_qq_media.py --image /mnt/c/Windows/Temp/shot.png --text "配文"
    python3 send_qq_media.py --file  /mnt/c/xxx/tool.zip --text "安装包"
    python3 send_qq_media.py --video /path/a.mp4 --text "成片"
    python3 send_qq_media.py --audio /path/a.mp3 --text "副歌"

为什么单独做成脚本：cron 任务跑在全新 session 里，没有当前对话；截图监控类任务
"有变化就把图推给他"必须能在两条命令内完成，不要每组都手写一遍 token+upload+send。

约定：
  - 凭据只读 ~/.hermes/.env，不打印、不落盘
  - msg_seq 每次不同（base + pid%5000），避免被去重
  - file_type：1 图片 / 2 视频 / 3 语音 / 4 普通文件（zip、pdf、xlsx 都走 4）
  - 必须有返回 message id，否则算没发出去（HTTP 200 不够）
"""
import argparse, base64, json, os, sys, urllib.request

ENV = os.path.expanduser("~/.hermes/.env")
DEFAULT_OID = "<OPENID>"   # 用户私聊 openid


def load_env(path):
    env = {}
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def token(env):
    data = json.dumps({"appId": env["QQ_APP_ID"],
                       "clientSecret": env["QQ_CLIENT_SECRET"]}).encode()
    req = urllib.request.Request("https://bots.qq.com/app/getAppAccessToken",
                                 data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["access_token"]


def send(tok, oid, payload, seq):
    payload["msg_seq"] = seq
    req = urllib.request.Request(f"https://api.sgroup.qq.com/v2/users/{oid}/messages",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"QQBot {tok}",
                                          "Content-Type": "application/json"},
                                 method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def upload(tok, oid, path, ftype):
    raw = open(path, "rb").read()
    body = {"file_type": ftype,
            "file_data": base64.b64encode(raw).decode(),
            "srv_send_msg": False}
    req = urllib.request.Request(f"https://api.sgroup.qq.com/v2/users/{oid}/files",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"QQBot {tok}",
                                          "Content-Type": "application/json"},
                                 method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=600).read())
    if "file_info" not in r:
        print("UPLOAD_FAILED " + json.dumps(r, ensure_ascii=False)[:300])
        sys.exit(3)
    return r["file_info"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="")
    ap.add_argument("--image", default="")
    ap.add_argument("--video", default="")
    ap.add_argument("--audio", default="")
    ap.add_argument("--file", default="")          # zip / pdf / xlsx 等普通文件
    ap.add_argument("--openid", default=DEFAULT_OID)
    a = ap.parse_args()

    tok = token(load_env(ENV))
    seq = 20000 + (os.getpid() % 5000)

    media = [(a.image, 1), (a.video, 2), (a.audio, 3), (a.file, 4)]
    media = [(p, t) for p, t in media if p and os.path.exists(p)]

    if media:
        path, ftype = media[0]
        info = upload(tok, a.openid, path, ftype)
        r = send(tok, a.openid, {"msg_type": 7, "media": {"file_info": info},
                                 "content": a.text or ""}, seq)
    elif a.text:
        r = send(tok, a.openid, {"msg_type": 0, "content": a.text[:1900]}, seq)
    else:
        print("nothing to send")
        sys.exit(1)

    if not r.get("id"):
        print("FAILED: no message id -> " + json.dumps(r, ensure_ascii=False)[:200])
        sys.exit(2)
    print("SENT " + r["id"])


if __name__ == "__main__":
    main()
