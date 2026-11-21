#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — 把 storyboard.json 注入 base.html，产出一个可渲染的单文件 HTML。

    python build.py examples/gravity.storyboard.json out.html

原理：base.html 里预留了 window.__STORYBOARD__ 钩子；
本脚本在 <head> 里插入一段 script，把分镜数据塞进去。
"""
import json, sys, os, io

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "templates", "base.html")


def main(sb_path, out_path):
    sb = json.load(open(sb_path, encoding="utf-8"))
    html = io.open(BASE, encoding="utf-8").read()

    if "__STORYBOARD__" not in html:
        sys.exit("base.html 缺少 __STORYBOARD__ 钩子")

    inject = ("<script>window.__STORYBOARD__ = "
              + json.dumps(sb["scenes"], ensure_ascii=False)
              + ";</script>\n</head>")
    html = html.replace("</head>", inject, 1)

    # 调色板也一并注入
    if sb.get("palette"):
        css = "".join(
            f"  --{k}: {v};\n" for k, v in sb["palette"].items()
            if k in ("bg", "ink", "dim", "accent")
        )
        html = html.replace(":root{", ":root{\n" + css, 1)

    io.open(out_path, "w", encoding="utf-8").write(html)

    total = sum(s.get("dur", 0) for s in sb["scenes"])
    print(f"OK  {out_path}")
    print(f"    镜头 {len(sb['scenes'])} 个，总时长 {total:.1f}s")
    print(f"    下一步: python scripts/render.py --html {out_path} "
          f"--duration {total:.1f} --fps {sb.get('fps',30)} --out film.mp4")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("用法: python build.py storyboard.json out.html")
    main(sys.argv[1], sys.argv[2])
