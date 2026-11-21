#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mux.py — 把无声 MP4 和 WAV 合成带音频的成片（顺带转 H.264，体积小一半）。

    python mux.py --video silent.mp4 --audio score.wav --out final.mp4 [--crf 20]

ffmpeg 查找顺序：
  1. 环境变量 FFMPEG
  2. 常见安装位置（Windows）
  3. PATH
"""
import argparse, os, shutil, subprocess, sys

CANDIDATES = [
    r"C:\Users\bx\AppData\Roaming\Seewo\EasiNote5\Dependencies\FFmpeg\FFmpeg_2\ffmpeg.exe",
    r"C:\Users\bx\AppData\Roaming\HaoCompress\Application\1.3.0.375\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    r"C:\ffmpeg\bin\ffmpeg.exe",
]


def find_ffmpeg():
    env = os.environ.get("FFMPEG")
    if env and os.path.exists(env):
        return env
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    w = shutil.which("ffmpeg")
    if w:
        return w
    sys.exit("找不到 ffmpeg：设置环境变量 FFMPEG，或用 --ffmpeg 指定")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crf", type=int, default=20, help="18=高画质，23=小体积")
    ap.add_argument("--abitrate", default="192k")
    ap.add_argument("--ffmpeg", default=None)
    a = ap.parse_args()

    ff = a.ffmpeg or find_ffmpeg()
    cmd = [
        ff, "-y", "-hide_banner", "-loglevel", "error",
        "-i", a.video, "-i", a.audio,
        "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", a.abitrate,
        "-shortest", "-movflags", "+faststart",
        a.out,
    ]
    print("ffmpeg:", ff)
    subprocess.run(cmd, check=True)
    mb = os.path.getsize(a.out) / 1024 / 1024
    print(f"OK  {a.out}  {mb:.1f} MB")


if __name__ == "__main__":
    main()
