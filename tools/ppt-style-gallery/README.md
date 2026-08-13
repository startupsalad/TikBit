# PPT 风格速查图册

> 一句话：**用眼睛挑 PPT 风格的图册**，60+ 个真实预览卡片，点一下把对应 prompt 拷到剪贴板，粘回给 AI 生成。不用再靠嘴描述"我想要什么审美"。

## 这是啥、从哪来

扒自开源 skill [`pakco77/pakco-html`](https://github.com/pakco77/pakco-html)（MIT 协议）里的**可视化选风格界面**（`style-picker.html`）。原 skill 是"HTML 演示文稿生成器"，其内核是我们**已经装了的两个 skill**：

- 骨架 = `html-ppt`（我们的 **C 模式**，36 主题 + 演讲者模式）
- 杂志/瑞士风 = `guizang-ppt`（我们的 **E 模式**）

所以整套 skill 没必要重装（内容 90% 重复）。**只把它比 C/E 多出来的那点价值——"看图挑风格"的界面——单独拎出来当图册用。** 这里不是 skill、不进 A~G 决策树，就是个本地图册。

## 怎么用（两步）

1. 双击 **`启动风格图册.bat`** —— 自动起本地服务器 + 弹浏览器。
2. 浏览器里翻 4 个标签（Skins 皮肤 / Templates 整套模板 / UI Taste / Social Cards 图文卡），
   看中哪个 → 点卡片 → prompt 自动进剪贴板 → 粘回给我（柚柚）/ 任意 AI，说"照这个风格做"。

> ⚠️ 必须走 `.bat` 起服务器再看，**别直接双击 html**——预览靠 iframe 加载子文件，`file://` 会被浏览器拦、卡片全白。
> 关掉那个黑窗口 = 停服务器。端口用的 8199，被占了就改 `.bat` 里的数字。

## 图册里有啥

| 标签 | 内容 | 数量 |
| :--- | :--- | :---: |
| 🎨 Skins | 换肤主题（同版式不同配色/字体） | 36 |
| 📑 Templates | 整套多页 deck（横版演示 + 竖版长页） | 23 |
| 🧩 UI Taste | UI 风格体系 | 4 |
| 🖼 Social Cards | 图文社交卡片风格 | 4 组 |

## 挑完风格之后 → 交给谁做

图册只负责"挑"，真正做 PPT 还是走我们自己的决策树（见 memory `ppt-five-mode-complete-integration`）：

- 挑中的是**演示/技术分享/带逐字稿** → 交 **C 模式 `html-ppt`**（同源，主题名直接对得上）
- 挑中的是**杂志风/瑞士风** → 交 **E 模式 `guizang-ppt`**
- 要**可编辑 PPTX / 标书 / 30 页+** → 该走 **B 模式 python-pptx**，图册风格仅作参考（这里只出 HTML，给不了 pptx）

## 已知边界

- 纯 HTML 图册，**不产 PPTX**、不导 PNG（原 skill 的 `render.sh` 写死 macOS Chrome 路径，Win 上用不了，已不纳入）。
- 只保留了 picker 运行必需的 `assets/` + `templates/`（1.3MB），原 repo 的大 gif/截图未拷。

---
来源 fork：`pakco77/pakco-html` ← 上游 `lewislulu/html-ppt-skill` + `op7418/guizang-*`。MIT，见 `LICENSE`。
