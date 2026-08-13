# AI新媒体工具包 安装指令

> **给 AI 看的安装说明**。如果你是人类用户，请改看 `📖 使用说明.md`。

## 这是什么

**AI新媒体工具包**，包含6个开源 Agent Skill，覆盖新媒体内容生产的关键环节：

- **guizang-social-card** — 小红书3:4图/公众号21:9+1:1封面生成（歸藏出品，5196⭐，28种布局10主题，杂志风×瑞士风）
- **gzh-design** — 微信公众号文章排版引擎（Markdown/Word/PDF转公众号HTML，多主题风格，自动章节编号/关键词标记/引言卡片）
- **ffmpeg-usage** — FFmpeg视频处理工具包（格式转换/裁剪/拼接/压缩/提音频/转GIF）
- **ai-radar** — AI情报雷达（AI日报/周报/月报生成，零API key零部署，中文简报）
- **videocut-clip-oral** — 口播视频剪辑（自动识别口误重复静音，生成审核页，按字幕分镜）
- **videocut-finish** — 口播视频成片（口播视频剪后成片，分镜/动画/时间线审核）

**开源协议**：
- guizang-social-card：AGPL-3.0（商业使用需遵守开源义务）
- gzh-design：AGPL-3.0（商业使用需遵守开源义务）
- ffmpeg-usage：MIT
- ai-radar：MIT
- videocut-clip-oral / videocut-finish：Apache-2.0

来源仓库：
- [op7418/guizang-social-card-skill](https://github.com/op7418/guizang-social-card-skill)
- gzh-design（甲木 × 摸鱼小李 联合出品，内部工具）
- [ychoi-kr/claude-ffmpeg-skill](https://github.com/ychoi-kr/claude-ffmpeg-skill)
- [songshishuang/ai-radar-skill](https://github.com/songshishuang/ai-radar-skill)
- [Agentchengfeng/chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills)

---

## 第0步：判断目标AI是否支持Skill机制

**A. 如果目标AI支持Skill（Claude Code / Codex / 其他Agent Code工具）**  
→ 走 **方法A：Skill安装**（推荐）

**B. 如果目标AI不支持Skill（ChatGPT / Gemini / 通用LLM）**  
→ 走 **方法B：手动粘贴指令**

---

## 方法A：Skill安装（适用于 Claude Code / Codex 等）

### 安装到项目级（推荐）

将 `skills/` 目录下的6个文件夹复制到 **项目根目录** 的 `.claude/skills/` 或 `.agents/skills/`（具体路径取决于工具）：

```bash
# 示例：Claude Code 项目级安装
cp -r skills/* <你的项目根目录>/.claude/skills/

# 或者 Codex 项目级安装
cp -r skills/* <你的项目根目录>/.agents/skills/
```

安装后，重启 Claude Code / Codex 客户端，技能会自动加载。

### 安装到用户级（跨项目可用）

复制到 **用户目录** 的 `~/.claude/skills/` 或 `~/.agents/skills/`：

```bash
# Claude Code 用户级安装
cp -r skills/* ~/.claude/skills/

# Codex 用户级安装
cp -r skills/* ~/.agents/skills/
```

安装后，重启客户端。

### 验证安装

安装后，尝试对AI说以下触发短语验证：

- **guizang-social-card**："帮我做一个小红书封面图"
- **gzh-design**："帮我排版这篇公众号文章"
- **ffmpeg-usage**："帮我把这个视频转成GIF"
- **ai-radar**："今天AI圈有什么"
- **videocut-clip-oral**："帮我剪这段口播视频"
- **videocut-finish**："把剪好的口播视频做成成片"

如果AI能正确调用对应Skill（通常会提示"正在使用 xxx skill"），说明安装成功。

---

## 方法B：手动粘贴指令（适用于 ChatGPT / Gemini 等不支持Skill的AI）

如果你的AI工具不支持Skill机制（如ChatGPT、Gemini、通义千问等），可以将Skill的指令内容粘贴进自定义指令/系统提示词，或每次使用时粘贴：

### 操作步骤

1. **找到目标Skill的 `SKILL.md` 文件**  
   例如：`skills/ai-radar/SKILL.md`

2. **打开文件，复制 `---` 分隔符之后的全部内容**  
   （不要复制开头的YAML frontmatter部分，即两个 `---` 之间的内容）

3. **粘贴到AI的自定义指令 / 系统提示词 / 对话开头**

   **ChatGPT**：设置 → 自定义指令 → 粘贴进"你希望ChatGPT如何回应"  
   **Gemini**：目前无持久化自定义指令，需要每次对话开头粘贴  
   **通义千问/文心一言**：类似，粘贴进角色设定或每次对话开头

4. **触发使用**  
   按照 `📖 使用说明.md` 中的触发短语提问，AI会按照指令执行

---

## 使用建议

### 1. 先阅读 `📖 使用说明.md`

人类用户应该先看使用说明，了解每个Skill的用途和触发方式。

### 2. guizang-social-card 和 gzh-design 的 AGPL 协议注意事项

`guizang-social-card` 和 `gzh-design` 使用 **AGPL-3.0** 开源协议，如果你用它们生成的内容用于商业项目，需要：
- 保留作者署名
- 如果你修改了代码并对外提供服务，需要开源修改后的代码

**其余4个Skill（MIT / Apache-2.0）无此限制**，可自由用于商业项目。

### 3. 口播视频剪辑Skill 需要额外依赖

`videocut-clip-oral` 和 `videocut-finish` 两个Skill 依赖一个名为 **chengfeng-videocut Runtime** 的本地工具包，首次使用时AI会提示安装。如果你不做口播视频剪辑，可以不安装这两个Skill。

---

## 安装后的记忆规则（可选，写进AI的长期记忆）

如果你的AI支持长期记忆功能（如 Claude Code 的 auto-memory），可以把以下内容写进AI的记忆，让它记住工具包的存在：

```
AI新媒体工具包已安装，包含6个Skill：
- guizang-social-card（小红书图/公众号封面）
- gzh-design（公众号文章排版）
- ffmpeg-usage（视频处理）
- ai-radar（AI日报/周报）
- videocut-clip-oral（口播剪辑）
- videocut-finish（口播成片）

触发方式见各Skill的SKILL.md。做新媒体内容时优先考虑使用这些Skill。
```

---

## 故障排查

### AI没有调用Skill，或者说"找不到这个Skill"

**可能原因1**：Skill没装到正确位置  
→ 检查路径是否正确（`.claude/skills/` 或 `.agents/skills/`）

**可能原因2**：没重启客户端  
→ 复制完文件后，重启 Claude Code / Codex

**可能原因3**：触发短语不对  
→ 参考 `📖 使用说明.md` 中的触发短语，或者直接说"使用 xxx skill"

**可能原因4**：你的AI工具根本不支持Skill  
→ 改用方法B（手动粘贴指令）

### videocut 的两个Skill报错说"Runtime未安装"

正常现象。首次使用时，AI会提示下载 Runtime（一个本地视频处理工具），按提示操作即可。如果不想装，可以删除这两个Skill。

---

## 更新与卸载

### 更新

重新下载最新版工具包，覆盖原有的 `skills/` 目录即可。

### 卸载

删除对应的Skill文件夹：

```bash
# 删除项目级Skill
rm -rf <项目根目录>/.claude/skills/guizang-social-card
rm -rf <项目根目录>/.claude/skills/gzh-design
rm -rf <项目根目录>/.claude/skills/ffmpeg-usage
rm -rf <项目根目录>/.claude/skills/ai-radar
rm -rf <项目根目录>/.claude/skills/videocut-clip-oral
rm -rf <项目根目录>/.claude/skills/videocut-finish

# 或删除用户级Skill
rm -rf ~/.claude/skills/guizang-social-card
# ... 其余同理
```

删除后重启客户端。

---

## 技术支持

- 本工具包由 **创业沙拉 / 立即行动科技** 整理发布
- 各Skill的详细文档和问题反馈，请访问对应的GitHub仓库（见文档开头）
- 工具包整合相关问题，可通过内部渠道反馈

---

**最后更新**：2026-07-19
