# 微蓝日报 视觉规范（来源：Refero「Origin Financial」设计系统）

> 产品经理指定参考：https://styles.refero.design/style/c60f05ff-2420-4a24-92db-80c4b6a74683
> 产品名「微蓝」= Blue Hour（黎明前天色微蓝的时刻），品牌语强调「在世界醒来之前，看见下一刻」。

## 品牌

- 中文名：微蓝日报
- 英文名：BLUE HOUR DAILY
- 品牌语（中文）：在世界醒来之前，看见下一刻。
- 品牌语（英文）：See what's next before the world wakes.

## 色彩（Dark 主题，中性深色底 + 蓝紫点缀）

### 品牌色
| Token | 值 | 用途 |
|---|---|---|
| Iris Gleam（主紫） | `#847dff` | 主强调色、分类卡 |
| Cyan Signal（青蓝） | `#00b3dd` | 数据强调、图表线条 |
| Pale Iris（浅紫） | `#d1c9ff` | 浅色面板 |
| Deep Iris（深紫） | `#4b49aa` | 深色面板/hover |
| Periwinkle（浅蓝） | `#90b8f0` | 蓝色分类卡 |
| Orchid Bloom（粉） | `#dd90d8` | 暖色对比卡 |

### 中性色（深）
| Token | 值 | 用途 |
|---|---|---|
| Obsidian | `#0f1011` | 页面画布（主深色底） |
| Abyss | `#090a0b` | 更深一层 |
| Graphite | `#2e2e2e` | 卡片表面 |
| Steel | `#3f4041` | hover/按压 |
| Silver | `#cacaca` | 浅色卡片/反白面板 |
| Fog | `#6a6b6b` | 弱化文字 |
| Ash | `#9f9fa0` | 正文/描述 |

### 中性色（浅）
| Token | 值 | 用途 |
|---|---|---|
| Cloud | `#f5f5f7` | 柔和的标题白 |
| Pure | `#ffffff` | 主文字/主操作 |
| Void | `#000000` | 图标/输入底 |

## 渐变（只允许这两条）

1. **Sky Atmosphere（蓝色天空，用于 hero）**
   `linear-gradient(rgb(15,16,17), rgb(19,29,39) 18%, rgb(26,71,136) 37%, rgb(64,138,193) 69%, rgb(64,138,193) 102%)`
2. **Dark Chrome（金属深色，用于设备框/抬升面）**
   `linear-gradient(135deg, rgb(43,43,44), rgb(19,19,19))`

规则：渐变不用于文字、按钮、功能卡；不用 radial/conic 渐变。

## 字体

- 展示标题：**Lyon Display**（衬线，weight 300，绝不加粗）→ 中文用系统衬线（Songti/Noto Serif SC）替代
- UI/正文：**Suisse Int'l**（无衬线）→ 中文用 PingFang SC / Microsoft YaHei
- 技术标签/数据：**Roboto Mono**（等宽，大写）

## 圆角

| 元素 | 圆角 |
|---|---|
| 按钮/输入/nav | 8px |
| 卡片/数据块 | 16px |
| 功能卡/分类卡 | 30px |
| pill 胶囊 | 9999px |

## 阴影与层次

- 以「表面颜色深浅变化」表达层次，几乎不用投影。
- 唯一阴影：`rgba(0,0,0,0.2) 0px 18px 20px`（单个按钮用）。
- 玻璃拟态：导航条 `backdrop-filter: blur(24px)`，`rgba(255,255,255,0.1)` 底 + 1px 白边。

## 动效

- 快速状态过渡：0.2s ease（背景色、透明度 hover/focus）。
- 长大气氛进场：2.5s cubic-bezier(0.455, 0.03, 0.515, 0.955)（hero 文字淡入）。
- 不弹跳、不 overshoot、不视差。

## 布局

- 全幅深色画布；内容容器 max-width 1200px；区块可通到边缘。
- 节奏：hero（氛围图 + 居中标题）→ 内容区块交替。
