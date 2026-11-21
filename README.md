# code-animation-skill

> 把一个抽象概念做成 1–2 分钟动画的 agent skill。
> 写 `storyboard.json` → 校验 → 渲染 → **自动质检**。

这是从《引力》那支片子里抽出来的完整流水线，装进 agent 就能复刻同一套质感。

成片与实验记录 → [gravity-code-animation](https://github.com/Shang-en-yee/gravity-code-animation)

---

## 为什么需要它

做第一支片子时，**八成的返工来自没有验收标准**：

- 以为"动感不够"是运动幅度问题，测了三轮才发现是信息密度问题
- 花最多力气做标注和结构，它们只贡献了 10% 的观感
- 换了个编码器，指标从 1.13 掉到 0.63，其实片子没变差

所以这个 skill 的重点不是代码，是**判断标准**：

| 文件 | 里面是什么 |
|---|---|
| `SKILL.md` | 完整流程 + 六层架构 + 五条血泪规则 |
| `reference/thresholds.json` | 四项可量化验收阈值 |
| `reference/findings.md` | 指标怎么设计、为什么这么调 |
| `reference/palette.json` | 配色与各层 alpha 的校准值 |
| `templates/shots/*.json` | 8 个镜头模板的参数 |
| `examples/gravity.storyboard.json` | 一支两分钟成片的完整分镜，可直接改文案 |

---

## 五步流程

```bash
python scripts/lint.py storyboard.json                          # 1. 校验分镜
python scripts/build.py storyboard.json out.html                # 2. 注入分镜
python scripts/render.py --html out.html --duration 117 \
       --fps 30 --out film.mp4                                  # 3. 渲染（0.5s/帧）
python scripts/measure.py --frames frames/                      # 4. 质检（测源帧）
python scripts/make_audio.py score.wav --storyboard storyboard.json   # 5. 配乐
python scripts/mux.py --video film.mp4 --audio score.wav --out final.mp4
```

`measure.py` 不达标会返回非零退出码——这是流水线能无人值守的关键。

---

## 验收阈值

```json
{ "frame_diff_min": 1.5, "moving_ratio_min": 0.70,
  "coverage_min": 0.20, "luma_range": [16, 30] }
```

| 指标 | 含义 | 低于下限会怎样 |
|---|---|---|
| `frame_diff` | 相邻帧平均差 | 变成幻灯片 |
| `moving_ratio` | 有运动的帧占比 | 卡顿感 |
| `coverage` | 有局部结构的像素占比 | 画面空 |
| `luma` | 平均亮度 | 低于 16 结构全沉在黑里；高于 30 丢掉暗调 |

**必须测源帧，不要测编码后的 MP4。** 这条有专门的说明。

---

## 八个镜头

| kind | 画面 |
|---|---|
| `title` / `outro` | 开篇 / 落版 |
| `orbit` | 椭圆轨道 + 极坐标网格 |
| `precess` | 进动花瓣线 + 角度盘 |
| `elevator` | 三维线框舱 + 下落粒子 |
| `warp` | 透视时空网格 + 引线标注 |
| `evidence` | 透镜同心环 + 啁啾波形 |
| `blackhole` | 3D 吸积盘 + 光子环 |

每个模板的参数和实测数据都在 `templates/shots/`。新镜头只写 L2，L1/L3 用现成的 `polarGrid` / `ringTicks` / `drawInstrument` / `drawLeader`。

---

## 五条血泪规则

1. **永远别用 `ctx.shadowBlur`** — 软件渲染下 5 秒/帧。用 1/6 降采样 bloom。
2. **参数必须同源** — 路径和头部由同一个变量驱动，否则元素会跑出线外。
3. **颗粒决定文件大小** — α=0.03 时 1080p30 约 50KB/帧。
4. **帧格式用 JPEG** — 带颗粒的 PNG 编码慢 4 倍。
5. **亮度不是滤镜** — 不要用 CSS brightness，要提内容层的 alpha。

---

## 安装

把整个文件夹放进 agent 的 skills 目录即可（结构符合 `SKILL.md` 规范）。

依赖：Python 3 + opencv-python + numpy（合成配乐还要 scipy）；渲染需要 Edge/Chrome；混音需要 ffmpeg（`mux.py` 会自动找常见路径，也可用 `FFMPEG` 环境变量指定）。

MIT License
