#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure.py — 质检。计算四项指标并与阈值比对。

**优先测源帧，不要测编码后的 MP4。**
编码器会改变像素差：mp4v 会保留颗粒和块效应，H.264 会把它们抹平。
同一份内容，mp4v 能测出 2.1，H.264 只有 1.5——测出来的不是内容，是编码器。
（这条是踩过的坑：换编码器后指标从 1.13 掉到 0.63，其实片子没变差。）

    python measure.py --frames frames/           # 推荐
    python measure.py film.mp4                   # 只能粗略参考

指标：
  frame_diff      相邻帧平均差（画面是否在动）
  moving_ratio    有运动的帧占比
  coverage        有局部结构的像素占比（信息密度）
  luma            平均亮度

退出码 0 = 全部达标；1 = 有指标未达标。
"""
import json, sys, glob, os, argparse
import cv2
import numpy as np


def iter_frames(src):
    if os.path.isdir(src):
        files = sorted(glob.glob(os.path.join(src, "*.jpg")) +
                       glob.glob(os.path.join(src, "*.png")))
        for f in files:
            im = cv2.imread(f)
            if im is not None:
                yield im
        return
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        sys.exit(f"打不开 {src}")
    while True:
        ok, im = cap.read()
        if not ok:
            break
        yield im
    cap.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="帧目录（推荐），或 MP4")
    ap.add_argument("--thresholds", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    th = {"frame_diff_min": 1.5, "moving_ratio_min": 0.70,
          "coverage_min": 0.20, "luma_range": [16, 30]}
    if a.thresholds:
        th.update(json.load(open(a.thresholds, encoding="utf-8")))

    prev = None
    diffs, lums, covs = [], [], []
    i = 0
    for im in iter_frames(a.source):
        small = cv2.cvtColor(cv2.resize(im, (640, 360)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        lums.append(float(small.mean()))
        if prev is not None:
            diffs.append(float(np.abs(small - prev).mean()))
        prev = small

        if i % 30 == 0:
            g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
            k = np.ones((15, 15), np.float32) / 225
            m = cv2.filter2D(g, -1, k)
            v = cv2.filter2D(g * g, -1, k) - m * m
            sd = np.sqrt(np.maximum(v, 0))
            covs.append(float(((sd > 2.5) | ((g - m) > 6)).mean()))
        i += 1

    if i < 2:
        sys.exit(f"{a.source} 里没有足够的帧")

    d = np.array(diffs)
    res = {
        "frames": i,
        "frame_diff": round(float(d.mean()), 2),
        "moving_ratio": round(float((d > 0.4).mean()), 3),
        "coverage": round(float(np.mean(covs)), 3),
        "luma": round(float(np.mean(lums)), 1),
    }

    lo, hi = th["luma_range"]
    checks = {
        "frame_diff":   (res["frame_diff"] >= th["frame_diff_min"], f">= {th['frame_diff_min']}"),
        "moving_ratio": (res["moving_ratio"] >= th["moving_ratio_min"], f">= {th['moving_ratio_min']}"),
        "coverage":     (res["coverage"] >= th["coverage_min"], f">= {th['coverage_min']}"),
        "luma":         (lo <= res["luma"] <= hi, f"{lo}–{hi}"),
    }
    ok = all(v[0] for v in checks.values())

    if a.json:
        print(json.dumps({**res, "pass": ok}, ensure_ascii=False))
        return 0 if ok else 1

    print(f"素材: {a.source}  ({res['frames']} 帧)")
    print("-" * 50)
    for k, (good, rule) in checks.items():
        print(f"  {'PASS' if good else 'FAIL'}  {k:<14} {res[k]:<8} 目标 {rule}")
    print("-" * 50)
    print("全部达标" if ok else "未达标：按 reference/findings.md 的调参顺序修改")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
