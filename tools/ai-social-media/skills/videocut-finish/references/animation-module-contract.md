# 动画模块契约

- 使用固定逻辑画布；尺寸由项目比例映射，不按预览窗口自适应成另一套布局。
- 根画面不可滚动；任一时间点必须是可确定复现的固定状态。
- 模块接收 `postMessage({ type: "set-step", step, time })`，并可从任意 `time` 直接恢复状态。
- 提供 `?static=1` 或定点 frame 检查入口；最终渲染禁用依赖墙钟的 CSS transition/animation。
- GSAP `from()` 状态必须在 seek 时恢复 opacity、transform 与 display，不能遗留透明元素。
- 预览和导出使用同一个 render URL、同一逻辑画布与安全区。
- 长网页使用截图视口、裁切或推拉缩放，不使用可滚动 iframe。
