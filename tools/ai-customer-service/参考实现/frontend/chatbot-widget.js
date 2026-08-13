/**
 * AI 在线客服机器人 · 前端聊天窗口（自注入，零依赖）
 * 由创业沙拉 TikBit 出品 · https://startupsalad.com
 *
 * 用法：在网站 </body> 前加一行——
 *   <script src="chatbot-widget.js"
 *           data-api="/guide-api/ask"
 *           data-title="在线咨询"
 *           data-subtitle="只答产品使用相关，复杂问题请联系我们"
 *           data-welcome="你好，有什么可以帮你？"
 *           data-fallback="咨询暂时连不上，请稍后再试或联系我们。"
 *           data-accent="#de283b"></script>
 *
 * 协议：POST data-api，发 {q:"问题"}，收 {answer:"回答"}。单轮问答，与后端一致。
 */
(function () {
  'use strict';
  var self = document.currentScript;
  function attr(k, d) { return (self && self.getAttribute('data-' + k)) || d; }

  var CFG = {
    api: attr('api', '/guide-api/ask'),
    title: attr('title', '在线咨询'),
    subtitle: attr('subtitle', '只答产品使用相关，复杂问题请联系我们'),
    welcome: attr('welcome', '你好，我是在线答疑助手 👋 产品使用上的问题都可以问我。'),
    fallback: attr('fallback', '咨询暂时连不上，请稍后再试，或通过页面上的联系方式找我们。'),
    accent: attr('accent', '#de283b'),
  };

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // ---- 注入样式（类名 ssc- 前缀 + 超高 z-index，不冲突现有页面）----
  var A = CFG.accent;
  var css = [
    '#ssc-fab{position:fixed;right:20px;bottom:20px;z-index:2147483000;background:' + A + ';color:#fff;border:none;border-radius:999px;padding:13px 20px;font-size:15px;font-weight:800;font-family:inherit;cursor:pointer;box-shadow:0 10px 28px -8px rgba(0,0,0,.4);display:flex;align-items:center;gap:8px;transition:.2s}',
    '#ssc-fab:hover{transform:translateY(-2px)}',
    '#ssc-panel{position:fixed;right:20px;bottom:20px;z-index:2147483001;width:min(380px,calc(100vw - 32px));height:min(560px,calc(100vh - 40px));background:#fff;border-radius:18px;box-shadow:0 20px 60px -12px rgba(0,0,0,.3);display:none;flex-direction:column;overflow:hidden;border:1px solid #eee;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}',
    '#ssc-panel.on{display:flex}',
    '.ssc-head{background:' + A + ';color:#fff;padding:15px 18px;display:flex;align-items:center;justify-content:space-between}',
    '.ssc-head .ttl{font-weight:800;font-size:15px}',
    '.ssc-head .ttl small{display:block;font-weight:400;font-size:11.5px;opacity:.85;margin-top:2px}',
    '.ssc-head .x{background:rgba(255,255,255,.2);border:none;color:#fff;width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:16px;line-height:1}',
    '.ssc-body{flex:1;overflow-y:auto;padding:16px;background:#fafafa;font-size:14px;line-height:1.7}',
    '.ssc-msg{margin:8px 0;display:flex}',
    '.ssc-msg.u{justify-content:flex-end}',
    '.ssc-msg .b{max-width:82%;padding:9px 13px;border-radius:12px;white-space:pre-wrap;word-break:break-word}',
    '.ssc-msg.a .b{background:#fff;border:1px solid #eee;color:#3d3d3d;border-bottom-left-radius:4px}',
    '.ssc-msg.u .b{background:' + A + ';color:#fff;border-bottom-right-radius:4px}',
    '.ssc-foot{border-top:1px solid #eee;padding:10px;display:flex;gap:8px;background:#fff}',
    '.ssc-foot textarea{flex:1;border:1px solid #e5e5e5;border-radius:10px;padding:9px 12px;font-size:14px;font-family:inherit;resize:none;height:40px;max-height:90px;outline:none}',
    '.ssc-foot textarea:focus{border-color:' + A + '}',
    '.ssc-foot button{background:' + A + ';color:#fff;border:none;border-radius:10px;padding:0 16px;font-weight:700;font-family:inherit;cursor:pointer}',
    '.ssc-foot button:disabled{opacity:.5;cursor:default}',
    '.ssc-dots span{display:inline-block;width:6px;height:6px;margin:0 2px;background:' + A + ';border-radius:50%;animation:sscb 1s infinite}',
    '.ssc-dots span:nth-child(2){animation-delay:.2s}.ssc-dots span:nth-child(3){animation-delay:.4s}',
    '@keyframes sscb{0%,60%,100%{opacity:.25}30%{opacity:1}}',
  ].join('');
  var styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ---- 构建 DOM ----
  var fab = document.createElement('button');
  fab.id = 'ssc-fab';
  fab.innerHTML = '💬 ' + esc(CFG.title);

  var panel = document.createElement('div');
  panel.id = 'ssc-panel';
  panel.innerHTML =
    '<div class="ssc-head"><div class="ttl">' + esc(CFG.title) + '<small>' + esc(CFG.subtitle) + '</small></div><button class="x">×</button></div>' +
    '<div class="ssc-body"></div>' +
    '<div class="ssc-foot"><textarea placeholder="输入问题，回车发送…" maxlength="500"></textarea><button class="send">发送</button></div>';

  document.body.appendChild(fab);
  document.body.appendChild(panel);

  var bodyEl = panel.querySelector('.ssc-body');
  var inputEl = panel.querySelector('textarea');
  var sendEl = panel.querySelector('.send');

  // ---- 交互 ----
  function add(cls, txt) {
    var m = document.createElement('div');
    m.className = 'ssc-msg ' + cls;
    var b = document.createElement('div');
    b.className = 'b';
    b.textContent = txt; // textContent 天然防 XSS
    m.appendChild(b);
    bodyEl.appendChild(m);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return b;
  }
  function typing() {
    var m = document.createElement('div');
    m.className = 'ssc-msg a';
    m.innerHTML = '<div class="b"><span class="ssc-dots"><span></span><span></span><span></span></span></div>';
    bodyEl.appendChild(m);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return m;
  }

  function open() { panel.classList.add('on'); fab.style.display = 'none'; inputEl.focus(); }
  function close() { panel.classList.remove('on'); fab.style.display = 'flex'; }
  fab.onclick = open;
  panel.querySelector('.x').onclick = close;

  add('a', CFG.welcome);

  var busy = false;
  function ask() {
    var q = inputEl.value.trim();
    if (!q || busy) return;
    busy = true; sendEl.disabled = true;
    add('u', q); inputEl.value = '';
    var t = typing();
    fetch(CFG.api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: q }),
    })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) { t.remove(); add('a', (d && d.answer) ? d.answer : CFG.fallback); })
      .catch(function () { t.remove(); add('a', CFG.fallback); })
      .finally(function () { busy = false; sendEl.disabled = false; inputEl.focus(); });
  }
  sendEl.onclick = ask;
  inputEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
  });
})();

