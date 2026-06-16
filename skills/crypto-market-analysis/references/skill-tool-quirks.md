# 技能工具已知坑与应对

> 这些是本技能开发/维护过程中发现的 Hermes 工具行为 quirks，供后续会话参考。

## skill_manage patch 的 "Unknown action ''" 错误

- **触发条件**：`old_string` 包含反引号 (`) 或长度超过约 500 字符时，skill_manage 有时会返回 "Unknown action ''. Use: create, edit, patch, delete, write_file, remove_file"
- **原因**：疑似 JSON 参数中转义问题
- **应对**：使用 skill_manage write_file 创建新文件，或分段用较短 old_string 分步 patch
- **替代方案**：创建独立 reference 文件替代直接修改 SKILL.md 长段落

## Yahoo Finance 盘后全部符号 ERR

- **位置**：`references/macro-enhanced-free.md` 中已记录
- **触发**：UTC 21:00 ~ 13:30（美股收盘后→盘前）
- **应对**：标注数据缺口，复用 session 中已有数据，不降级

## Deribit mark_iv 单位

- **位置**：`references/deribit-options.md` 中已记录（坑 1）
- **关键**：返回 0.2715 = 27.15%，打印时用 `f'{iv*100:.1f}%'`，存储时用原始值
- **常见错误**：`iv = mark_iv * 100` 再做计算 → 得到 absurd 值
