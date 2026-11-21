---
name: code-animation
description: "用代码生成 1–2 分钟的中文科普动画（代码驱动动效）。给定故事梗概，产出 storyboard.json，渲染成 MP4，并用可量化指标自动质检。适用于物理/数学概念讲解、技术演示、数据叙事；当用户要求制作代码动画、科普短片、概念可视化视频，或说"把某个概念做成动画"时触发。"
license: MIT
type: tool
tags: ["animation", "video", "canvas", "storyboard", "science", "科普"]
---

# 代码动画工坊（Code Animation）

把一个抽象概念做成 1–2 分钟的动画短片。**不是生成式视频**——每一帧都是浏览器里算出来的矢量画面，可逐帧复现、可局部修改。

产物是一个 MP4，加一份可复用的 storyboard.json。

---

## 三步流程

```bash
# 1. 校验分镜
python scripts/lint.py storyboard.json

# 2. 构建 + 渲染（约 0.5 秒/帧）
python scripts/build.py storyboard.json out.html
python scripts/render.py --html out.html --duration 117 --fps 30 --out film.mp4

# 3. 质检，不达标会返回非零
python scripts/measure.py film.mp4 --thresholds reference/thresholds.json
```

质检不过就改，不要靠"看着还行"验收。

### 加配乐（可选，但强烈建议）

音频同样是**算出来的**，不采样任何素材库——和画面一个道理。

```bash
# 1. 合成配乐（numpy，约 40 秒）
python scripts/make_audio.py score.wav --storyboard storyboard.json

# 2. 合进视频，顺带转 H.264 压体积
python scripts/mux.py --video film.mp4 --audio score.wav --out final.mp4 --crf 23
```

**默认配乐是太空/物理题材的底**：D 小调长音铺底 + 每镜换和弦的 pad + 8 秒一次的心跳脉冲 + 稀疏拨弦，转场处有噪声扫频、章节处有低频落点。

换题材时要换配乐参数，不要直接套：

| 题材 | 配乐改法 |
|---|---|
| 物理 / 天文 | 保留默认：小调、长音、稀疏 |
| 数学 / 算法 | 换成大调或里底亚调式，加一点规律性的琶音 |
| 历史 / 人文 | 去掉脉冲，pad 变慢，加一点不协和音程 |
| 产品 / 技术 | 去掉 pad 长音，改成 90–110 BPM 的合成器律动 |

参数都在 `make_audio.py` 顶部的 `SCALE` / `ROOT` / `bpm` 三个常量，和 `build()` 里的 `chords` 数组。

---

## storyboard.json

```json
{
  "title": "引力",
  "fps": 30,
  "palette": { "bg": "#08090F", "ink": "#E6DCCB", "dim": "#8A8177", "accent": "#E0813C" },
  "scenes": [
    {
      "id": "open",
      "kind": "title",
      "dur": 6.0,
      "cn": "引力",
      "en": "GRAVITY"
    },
    {
      "id": "newton",
      "kind": "orbit",
      "dur": 16.0,
      "chapter": ["I", "苹果与月亮", "THE APPLE AND THE MOON"],
      "subs": [
        [0.6,  "1687 年，牛顿用一个公式，把苹果和月亮绑在了一起。"],
        [7.4,  "引力与质量成正比，与距离的平方成反比。"]
      ]
    }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `kind` | 镜头模板名，见下表 |
| `dur` | 该镜时长（秒），建议 12–20 |
| `chapter` | `[序号, 中文, ENGLISH]`，左上角常驻 |
| `subs` | `[起始秒, 文本]` 数组；每屏逗留 5–6 秒为宜 |
| `cn` / `en` | 标题类镜头用 |

---

## 镜头模板（8 个）

| kind | 画面 | 适用 |
|---|---|---|
| `title` | 大字 + 英文小标 | 开篇 |
| `outro` | 两行结论 | 落版 |
| `orbit` | 椭圆轨道 + 极坐标网格 | 周期运动、引力 |
| `precess` | 进动花瓣线 + 角度盘 | 微小偏差、进动 |
| `elevator` | 方框 + 内部刻度 | 参照系、等效原理 |
| `warp` | 透视时空网格 + 引线标注 | 弯曲、场 |
| `evidence` | 透镜同心环 + 啁啾波形 | 证据、信号 |
| `blackhole` | 吸积盘 + 光子环 + 环形刻度 | 极端天体 |

模板参数见 `templates/shots/*.json`。

---

## 六层架构（为什么这么排）

```
L5 后期    bloom → 暗角 → 颗粒
L4 文字    章节标 / 大字 / 公式 / 字幕
L3 标注    引线 + 小标签 + 读数框
L2 主体    本镜核心图形
L1 结构    网格 / 刻度 / 坐标轴
L0 背景    星云 / 点阵 / 尘埃 / 远星
```

**L1 和 L3 是"专业感"的来源**，不是 L2。一个只有主体的画面会显得简陋；加上结构层和标注层，同一张图立刻变成"仪器界面"。

`base.html` 已经实现全部六层，新镜头只要写 L2 的绘制函数。

---

## 验收阈值

`reference/thresholds.json`：

```json
{
  "frame_diff_min": 1.5,
  "moving_ratio_min": 0.70,
  "coverage_min": 0.20,
  "luma_range": [16, 30]
}
```

| 指标 | 含义 | 为什么 |
|---|---|---|
| `frame_diff` | 相邻帧平均差 | 低于 1.5 就是"幻灯片"，不是动画 |
| `moving_ratio` | 有运动的帧占比 | 低于 70% 会有"卡住"感 |
| `coverage` | 有局部结构的像素占比 | 低于 20% 画面显得空 |
| `luma` | 平均亮度 | 低于 16 时结构全沉在黑色里；高于 30 会丢掉暗调基调 |

**这些阈值是用真实参考片校准出来的，别随便调高。** 详见 `reference/findings.md`。

---

## 已知坑（血泪）

**1. 永远不要用 `ctx.shadowBlur`。**
软件渲染下几十处逐帧阴影会把单帧从 20ms 拖到 5 秒。用 `base.html` 里的 `bloom()` —— 画布缩到 1/6 再放大叠加，两次 `drawImage`，几乎免费。

**2. 参数必须同源。**
曾经出现过"质点跑在线外面"的 bug：线用 `p²` 算，点用 `p` 算。**同一元素的路径和头部必须由同一个变量驱动。**

**3. 颗粒决定文件大小。**
逐帧随机噪点熵极高，视频编码器压不动。颗粒 α=0.03 时 1080p30 约 50KB/帧——两分钟片子约 300MB。
要小就降 α（0.015 左右）或降帧率，别指望编码器。

**4. 帧格式用 JPEG，不要 PNG。**
带颗粒的 PNG 编码耗时是 JPEG 的 4 倍以上（实测 2.0s/帧 vs 0.5s/帧）。

**5. 亮度不是滤镜。**
不要用 CSS `brightness()` 提亮——会把文字一起吹白。要提亮就提**内容层**的 alpha（网格、星云、尘埃），按 `reference/palette.json` 的配比来。

---

## 扩展新镜头

1. 在 `base.html` 的 `drawScene()` 里加一个 `case`
2. 只写 L2（主体）；L1 用 `polarGrid` / `ringTicks` / `axisTicks` / `drawInstrument`，L3 用 `drawLeader`
3. 把可调项抽成参数对象，存到 `templates/shots/<name>.json`
4. 跑 `measure.py`，三个指标达标才算完成

---

## 例子

`examples/gravity.storyboard.json` —— 两分钟成片《引力》的完整分镜，八个镜头全部实拍可用。可作为起点直接改文案。
