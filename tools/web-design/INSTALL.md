# 网页设计套件安装与更新

## 先确认范围

先读取仓库根 README 和 catalog.json，介绍用途并等待用户确认本工具。明确安装目标知识库及要使用的引擎；现有工具可用时不重复安装，用户要求升级才处理对应更新。

## 工作台安装（优先）

支持该入口的客户端使用“设置 → 更多工具 → 网页设计套件 → 安装／更新／修复”，客户端按目录声明校验包大小、SHA256 和逐文件哈希，将同一套文件装到当前知识库的 .claude/skills/ 和 .agents/skills/。保留现有自定义修改和可回退版本，不擅自覆盖。安装完成后用“立即使用”打开新对话；未执行真实任务时只报告文件安装状态。

## AI 从源码安装（兼容入口）

不需要旧版原始安装包、install-core.js 或写入用户全局配置。

1. 读取 tools/web-design/VERSION 与 skills/ 下三个 Skill 的完整说明。当前应包含 web-design-engineer、frontend-design、unslop，以及各自引用的资源与许可证。
2. 默认以已确认知识库的 .claude/skills/ 为 Claude 项目目录，.agents/skills/ 为 GPT／Codex 项目目录。仅当用户选择用户级安装时，才按实际 CLAUDE_CONFIG_DIR／CODEX_HOME 定位，不猜固定用户目录。
3. 先比已有内容。缺失目录直接复制完整 Skill；已有完全相同文件跳过；不同内容须识别是否自定义或旧受管版本，备份并经用户选择后更新，不用整目录覆盖。
4. 每个安装的 Skill 在自己的 resources/ 下补齐本工具的设计大脑/ 和 README.md，保留原相对结构；源码执行文件优先查同一 Skill 的 resources/设计大脑/，再按实际位置定位原设计大脑。unslop 自带 references/、参考图、scripts/、agents/ 和 LICENSE，全部复制，不能只安装 SKILL.md。
5. 回读两边 SKILL.md、unslop/references/usage-boundaries.md、LICENSE 和实际引用；确认来源目录与安装文件一致。可用本仓库的声明式包作为同样结构的安装来源，但须核 manifest.json、版本、文件大小和 SHA256。不要执行包外的远程安装脚本。
6. 对保留自定义 frontend-design 的用户，明确告知可直接自然语言调用 unslop；不为新增路由强改用户既有 Skill。所有新路径按目标环境实际位置处理。

## 验收与依赖

- 安装检查：两端分别存在三个入口，资源可读，unslop 相对链接可解析，许可证和参考图未漏。用户只选择单引擎时说明已覆盖范围。
- 新对话测试：“用 unslop 检查这个页面，先列问题，不改代码。”应先读项目执行边界并遵循品牌与业务保护；不能把文件存在等同于真实新对话已加载。
- 诊断和改稿不要求额外购买服务。snapshot.mjs 需要 Node.js、Playwright／playwright-core 及浏览器；story.mjs 另需 ffmpeg。先复用已有宿主依赖，缺失按具体任务说明，不静默下载大依赖或调用付费素材服务。
- Mac／Windows 原生效果、登录页面快照及录制等没实跑的范围须明确，不以另一平台或语法检查替代。

## 发布与用户更新的区别

本地改源文件、GitHub 已发布、上海 OSS 已同步、用户已更新与新对话已加载是独立状态。源码变化须升 VERSION，构建独立包并发布包后发布清单，再运行既有 OSS 同步流程；没有自动发布流水线时不能说“Git 改了用户就有”。不改旧版已发布包，也不自动覆盖客户 Skill。
