---
name: UNDocsSearcher
description: 独立检索联合国文件（UNITE 网站索引与 ODS 集合），按关键词查找联合国文件/新闻记录，并可按正式文号下载 ODS PDF 和提取文本。
---

# UNDocsSearcher

> **`<skill-dir>`** = 本 SKILL.md 所在目录。核心脚本为 `<skill-dir>/scripts/undocs_search.py`；Windows 用 `<skill-dir>/run.ps1`，macOS/Linux 用 `<skill-dir>/run.sh`。部署与排错见 [README.md](README.md)。

这个 skill 只做联合国文件这一个来源族：

- `search --collection un`：`search.un.org` 的 UNITE 网站索引，包含文件、网页和新闻；
- `search --collection ods`：ODS 集合的元数据检索；
- `fetch <symbol>`：按正式文号通过 `documents.un.org/api/symbol/access` 下载 PDF，并提取逐页文本；
- `fetch <URL>`：读取 search.un.org / documents.un.org 返回的页面或 PDF。

## 命令

```powershell
& '<skill-dir>/run.ps1' search "charter" --collection un --limit 10 --out './unite.json'
& '<skill-dir>/run.ps1' search "genocide" --collection ods --limit 10 --out './ods.json'
& '<skill-dir>/run.ps1' fetch "A/RES/70/1" --pdf-out './ar701.pdf' --text-out './ar701.txt' --out './fetch.json'
& '<skill-dir>/run.ps1' doctor
```

通用参数：`--out`、`--cache`、`--cache-ttl`、`--offline`、`--timeout`。`search` 另有 `--collection un|ods`、`--limit`、`--offset`；`fetch` 另有 `--text-out`、`--pdf-out`、`--max-mb`。

## 结果边界

- `collection=un` 是 UNITE 网站索引，**可能包含新闻和网页**，不等于 ODS 文号库；`status=fallback` 会明确标注。
- `collection=ods` 的关键词检索仍可能只有计数而没有 docs；适配器会报错，不会把缺失 docs 解释成零结果。
- `fetch <symbol>` 只从 ODS 按文号取 PDF；符号格式错误、文件不存在或语言版本缺失会保留为错误。
- `total` 是 UNITE/ODS 返回的 `numberDocsFound`，不是本机已取得全文的数量。

## 参考

- 2026-11-09 实测：`collection=un`、`ods`、ODS 文号 PDF 下载：[references/undocs-search.md](references/undocs-search.md)
- 部署、环境与排错：[README.md](README.md)
