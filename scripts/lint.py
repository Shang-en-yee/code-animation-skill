#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint.py — 校验 storyboard.json

检查项：
  * 必填字段 / 未知 kind / 重复 id
  * dur 是否在 8–25 秒（太短交代不清，太长会闷）
  * subs 是否按时间递增、是否过密或过疏
  * 单屏字数是否超限（中文一屏 ≤ 40 字，超过必崩）
  * 总时长是否在 90–180 秒

退出码 0 = 通过，1 = 有问题。
"""
import json, sys, os

KNOWN_KINDS = {"title", "outro", "orbit", "precess", "elevator",
               "warp", "evidence", "blackhole"}

MAX_SUB_CHARS = 40          # 单屏字幕字数上限
SUB_GAP_MIN, SUB_GAP_MAX = 3.0, 8.0   # 相邻字幕间隔（秒）
DUR_MIN, DUR_MAX = 8.0, 25.0
TOTAL_MIN, TOTAL_MAX = 90.0, 180.0


def main(path):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"[FAIL] 读不了 {path}: {e}"); return 1

    errs, warns = [], []
    scenes = data.get("scenes") or []
    if not scenes:
        print("[FAIL] scenes 为空"); return 1

    ids = set()
    total = 0.0
    for i, sc in enumerate(scenes):
        tag = f"场景#{i+1}({sc.get('id','?')})"
        sid = sc.get("id")
        if not sid: errs.append(f"{tag}: 缺 id")
        elif sid in ids: errs.append(f"{tag}: id 重复")
        else: ids.add(sid)

        kind = sc.get("kind")
        if kind not in KNOWN_KINDS:
            errs.append(f"{tag}: 未知 kind '{kind}'，可选 {sorted(KNOWN_KINDS)}")

        dur = sc.get("dur")
        if not isinstance(dur, (int, float)):
            errs.append(f"{tag}: dur 缺失或非数字")
        else:
            total += dur
            if not (DUR_MIN <= dur <= DUR_MAX):
                warns.append(f"{tag}: dur={dur}s 超出建议区间 {DUR_MIN}-{DUR_MAX}")

        if kind in ("title", "outro"):
            if not sc.get("cn"): errs.append(f"{tag}: {kind} 需要 cn")

        if kind not in ("title", "outro"):
            if not sc.get("chapter"):
                warns.append(f"{tag}: 没有 chapter，左上角会空着")

        subs = sc.get("subs") or []
        prev_t = -1
        for k, item in enumerate(subs):
            if not (isinstance(item, list) and len(item) == 2):
                errs.append(f"{tag}: subs[{k}] 应为 [秒, 文本]"); continue
            t, txt = item
            if t <= prev_t:
                errs.append(f"{tag}: subs 时间未递增（{t} <= {prev_t}）")
            prev_t = t
            if len(txt) > MAX_SUB_CHARS:
                warns.append(f"{tag}: 字幕 {len(txt)} 字，超过 {MAX_SUB_CHARS}，建议拆行")
            if dur and t > dur - 1.5:
                errs.append(f"{tag}: subs[{k}] 起始 {t}s 太靠镜尾，来不及读完")
        # 间隔检查
        for k in range(1, len(subs)):
            gap = subs[k][0] - subs[k-1][0]
            if gap < SUB_GAP_MIN:
                warns.append(f"{tag}: 字幕间隔 {gap:.1f}s 过密（<{SUB_GAP_MIN}）")
            if gap > SUB_GAP_MAX:
                warns.append(f"{tag}: 字幕间隔 {gap:.1f}s 过长（>{SUB_GAP_MAX}），画面会空")

    if not (TOTAL_MIN <= total <= TOTAL_MAX):
        warns.append(f"总时长 {total:.1f}s 超出建议 {TOTAL_MIN}-{TOTAL_MAX}")

    for w in warns: print("[warn]", w)
    for e in errs: print("[ERROR]", e)

    if errs:
        print(f"\n未通过：{len(errs)} 个错误，{len(warns)} 个警告"); return 1
    print(f"\n通过：{len(scenes)} 个镜头，总时长 {total:.1f}s，{len(warns)} 个警告")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法: python lint.py storyboard.json")
    sys.exit(main(sys.argv[1]))
