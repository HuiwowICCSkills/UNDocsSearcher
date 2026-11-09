# 联合国文件检索实测记录（2026-11-09）

## UNITE

`https://search.un.org/api/search`

参数：`collection=un|ods`、`q`、`row=10`、`sort=relevance`、`currentPageNumber`。

实测 `charter --collection un --limit 2` → `status=fallback`、`total=1000`、2 条；结果可能包含网页和新闻。

## ODS 文号

`https://documents.un.org/api/symbol/access?s=A%2FRES%2F70%2F1&l=E`

实测 `fetch A/RES/70/1` → `status=ok`、35 页 PDF、`needs_ocr=false`。

## 边界

- `collection=ods` 的关键词检索可能只有 `numberDocsFound` 而没有 `docs`；适配器会报错而不是返回空结果。
- `collection=un` 是 UNITE 网站索引，不等于 Digital Library 或 ODS。
