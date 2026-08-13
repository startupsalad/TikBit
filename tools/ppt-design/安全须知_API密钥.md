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

**用户需要自己配置密钥**：

**方式 1：环境变量（推荐）**
```bash
export GPT_API_KEY="用户自己的密钥"
export GPT_BASE_URL="https://api.openai.com/v1"
```

**方式 2：配置文件**
在脚本所在目录创建 `gpt_config.md`：
```markdown
---
api_key: 用户自己的密钥
base_url: https://api.openai.com/v1
image_model: gpt-image-2
---
```

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
- 需要自己的 OpenAI API 密钥
- 按上述方式 1 或方式 2 配置
- AI 会在需要时自动调用

---

**分发版本已确保无密钥泄露风险 ✅**
