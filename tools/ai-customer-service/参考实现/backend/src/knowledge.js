// 知识库加载：读取 knowledge-base/ 目录下所有 .md / .txt 文件并拼接
// 由创业沙拉 TikBit 出品 · https://startupsalad.com

const fs = require('fs');
const path = require('path');

/**
 * 加载知识库目录下所有文本，拼成一个字符串
 * @param {string} dir - 知识库目录绝对路径
 * @param {number} maxChars - 上限字符数，超出会截断并告警（默认 20000）
 * @returns {string}
 */
function loadKnowledge(dir, maxChars = 20000) {
  if (!fs.existsSync(dir)) {
    console.warn(`[knowledge] 目录不存在: ${dir}，知识库为空`);
    return '';
  }
  const files = fs
    .readdirSync(dir)
    .filter((f) => /\.(md|txt)$/i.test(f))
    .sort();

  let out = '';
  for (const f of files) {
    const content = fs.readFileSync(path.join(dir, f), 'utf-8');
    out += `\n\n===== ${f} =====\n${content}`;
  }

  if (out.length > maxChars) {
    console.warn(
      `[knowledge] 知识库 ${out.length} 字符，超过上限 ${maxChars}，已截断。建议精简或改用 FAQ 问答对。`
    );
    out = out.slice(0, maxChars);
  }
  console.log(`[knowledge] 已加载 ${files.length} 个文件，共 ${out.length} 字符`);
  return out;
}

module.exports = { loadKnowledge };

