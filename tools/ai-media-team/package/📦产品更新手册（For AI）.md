# 📦 新媒体AI员工 · 更新说明（给 AI 读）

> **这份说明是给「用户电脑里的 Claude」看的。**
> 老用户下载了新版产品包后，把它交给你、说"帮我更新一下"，你照本说明把系统文件更新到最新，同时**完整保留用户的配置和作品**。

---

## 第零原则

你是聪明的更新者：**只更新系统文件（skill + 工具箱通用文件），绝不碰用户数据**（配置文件、收集箱、素材原料库、选题库、作品、经验库）。更新前先备份，每一步可逆。

---

## 更新步骤

### Step 1：确认已安装

```bash
ls -la "新媒体AI员工/" 2>/dev/null
ls -la ~/.claude/skills/ | grep -E "director|总监"
ls -la ~/.codex/skills/ 2>/dev/null | grep -E "director|总监"   # GPT 侧（双模型）
```

> **双模型（2026-07 起）**：三位总监同时装在 `~/.claude/skills/`（Claude）和 `~/.codex/skills/`（GPT）。更新时两处都要覆盖。老用户若只有 Claude 侧，这次更新会顺带补上 GPT 侧。

- 找不到 → 用户是新用户，请改用 `【给AI读】安装说明.md` 做首次安装。
- 找到了 → 继续。

### Step 2：备份用户数据（防误操作）

```bash
backup_dir="新媒体AI员工_备份_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp "新媒体AI员工/我的新媒体AI员工.md" "$backup_dir/" 2>/dev/null
cp -r "新媒体AI员工/策划总监" "$backup_dir/" 2>/dev/null
cp -r "新媒体AI员工/内容总监" "$backup_dir/" 2>/dev/null
cp -r "新媒体AI员工/制作总监" "$backup_dir/" 2>/dev/null
echo "✅ 已备份到 $backup_dir"
```

告诉用户备份位置，再继续。

### Step 3：更新三个 skill（覆盖到最新）

新版产品包解压后，里面有 `新媒体AI员工/📦临时skill文件夹/`。把它的三个总监覆盖安装到 skills 目录：

```bash
# 两个大脑各一份：Claude 用 ~/.claude/skills，GPT 用 ~/.codex/skills
for base in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
  mkdir -p "$base"
  # 删旧（兼容中英文命名）
  rm -rf "$base/marketing-director" "$base/content-director" "$base/creative-director"
  rm -rf "$base/策划总监" "$base/内容总监" "$base/制作总监"
  # 装新（统一英文名）——路径指向你刚解压的新版产品包
  cp -r "新媒体AI员工/📦临时skill文件夹/策划总监" "$base/marketing-director"
  cp -r "新媒体AI员工/📦临时skill文件夹/内容总监" "$base/content-director"
  cp -r "新媒体AI员工/📦临时skill文件夹/制作总监" "$base/creative-director"
done
# 若这台机器没装 GPT(Codex)、没有 ~/.codex 目录，上面那份会自动跳过创建也无妨；只装 Claude 侧不影响使用。
```

> ⚠️ 如果新版产品包解压在别处（不在 vault 里），把上面 `cp` 的源路径换成新包的实际位置。

### Step 4：更新工具箱（系统文件覆盖，素材不覆盖）

```bash
# 通用系统文件（脚本/模板/规则）：覆盖到最新
cp -r "<新版产品包>/工具箱/"*.md "<新版产品包>/工具箱/"*.py "新媒体AI员工/工具箱/" 2>/dev/null
cp -r "<新版产品包>/工具箱/能力提升计划" "新媒体AI员工/工具箱/" 2>/dev/null

# 素材库：用 -n 不覆盖（保住用户自己加的素材/已填的品牌素材）
cp -rn "<新版产品包>/工具箱/📦素材库/"* "新媒体AI员工/工具箱/📦素材库/" 2>/dev/null
echo "✅ 工具箱更新完成"
```

（把 `<新版产品包>` 换成你解压新版包的实际路径。如果新包就在 vault 里、和旧的同名，注意别自己覆盖自己——必要时先把新包解压到临时目录再 cp。）

### Step 5：清理临时文件

```bash
rm -rf "<新版产品包>/📦临时skill文件夹"
rm -f "<新版产品包>/【给AI读】安装说明.md" "<新版产品包>/📦产品更新手册（For AI）.md"
```

### Step 6：验证

让用户分别说"蛋总上线""艾AA上线""柳如是上线"，三位都能正常出场即更新成功。**提醒用户重启 Claude Code 后再测**（skill 启动时加载）。

### Step 7：完成通知

```
✅ 更新完成！三位总监已升级到最新版。
你的配置、作品、经验库都原样保留了。
备份在：[备份文件夹路径]，确认没问题后可删。
```

---

## 更新原则

| 文件类型 | 策略 |
|---------|------|
| skill（三总监） | 覆盖到最新 |
| 工具箱通用文件（.md/.py/读书计划） | 覆盖到最新 |
| 素材库 | 用户没有的添加，已有的不覆盖 |
| **配置文件 `我的新媒体AI员工.md`** | **保留不动** |
| **数据文件**（收集箱/素材原料库/选题库/发布记录/经验库） | **保留不动** |
| **作品文件夹** | **保留不动** |

向后兼容：新版 skill 能读旧版配置和数据；如有不兼容变更，会在更新说明里标注。

---

**更新完成后，本说明文件可以删除。**
