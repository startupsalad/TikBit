# 🔒 安全须知：API 密钥配置

> **本工具包是分发版本，不包含任何 API 密钥**

---

## 重要说明

本工具包中的所有脚本**不含明文密钥**，密钥留空由用户自行配置。

### GPT 工具包（A 模式）

**文件位置**：`工具脚本/GPT工具包/GPT做PPT工具.py`

**默认配置**：
```python
cfg = {"base_url": "", "api_key": "", "image_model": "gpt-image-2"}
```

**密钥来源：复用 TikBit 工作台令牌**

A 模式的生图走创业沙拉 TikBit 中转站，和 `gpt-image` 工具包是同一套脚本、同一个接口。**不需要另外申请 OpenAI 密钥**，AI 安装时会复用工作台已配置的令牌：

- 读环境变量 `ANTHROPIC_AUTH_TOKEN`，或本机 Claude 配置 `settings.json` 的 `env` 字段
- 确认 `ANTHROPIC_BASE_URL` 主机是 `tikbit.ai` 才可复用
- 生图消耗的是工作台同一份额度

**方式 1：配置文件（脚本的唯一配置源）**

在脚本所在目录的 `GPT配置.md` 写入 YAML frontmatter：
```markdown
---
base_url: https://tikbit.ai/v1
api_key: 复用的工作台令牌
image_model: gpt-image-2
---
```

> ⚠️ 文件名必须是 `GPT配置.md`。脚本里写死的是 `CONFIG_FILE = SCRIPT_DIR / "GPT配置.md"`，叫 `gpt_config.md` 读不到，会一直提示没配 API。

**方式 2：环境变量（覆盖配置文件）**
```bash
export GPT_API_KEY="TikBit 令牌"
export GPT_BASE_URL="https://tikbit.ai/v1"
```

> `base_url` 必须带 `/v1`。脚本会在其后拼接 `/images/generations`，缺少 `/v1` 会 404。

### Space Multi Design PPT（G 引擎）

**需要 Node.js**（用于 `npx getdesign` 拉取品牌设计规范）

**不需要 API 密钥**（getdesign.md 是公开数据源）

### 其他模式

| 模式 | 需要密钥 |
|:---:|:---:|
| **B** 可编辑 PPTX | ❌ 不需要 |
| **C** HTML slides | ❌ 不需要 |
| **D** 多代理评审 | ⚠️ 需要 Claude API（但由用户 AI 环境提供） |
| **E** 杂志风 | ❌ 不需要 |
| **F1** 文档转换 | ❌ 不需要 |
| **F2** 复杂转换 | ⚠️ 需要 Claude API（但由用户 AI 环境提供） |
| **G** 品牌风格 | ❌ 不需要（仅需 Node.js） |

---

## 给分发者的检查清单

在分发本工具包前，确认：

- [ ] ✅ GPT 工具包的配置文件已删除或清空密钥
- [ ] ✅ 没有 `.env` 文件包含密钥
- [ ] ✅ README_AI_INSTALL.md 已说明密钥配置方式
- [ ] ✅ README_USER.md 已提醒用户自行配置

---

## 给使用者的说明

**如果你不用 GPT 生图（A 模式）**：
- 不需要配置任何密钥
- 其他 7 种模式（B/C/D/E/F1/F2/G）都能正常使用

**如果你要用 GPT 生图（A 模式）**：
- 不用另找 OpenAI 密钥，AI 会复用你 TikBit 工作台的令牌
- 工作台没配令牌时，去 tikbit.ai 后台「令牌管理」取一个，按上述方式 1 填进 `GPT配置.md`
- 配好后 AI 会在需要时自动调用，生图走工作台同一份额度

---

**分发版本已确保无密钥泄露风险 ✅**
