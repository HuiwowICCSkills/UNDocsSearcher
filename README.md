# UNDocsSearcher 部署指引

独立检索联合国文件（UNITE/ODS），并可按文号下载 PDF。主要访问 `search.un.org` 与 `documents.un.org`。

仓库：<https://github.com/HuiwowICCSkills/UNDocsSearcher>（公开）。

## 环境

Python 3.10+，依赖 `requests`、`beautifulsoup4`、`pypdf`；无需登录。

## 安装与自检

```powershell
git clone https://github.com/HuiwowICCSkills/UNDocsSearcher.git "$env:USERPROFILE\.codex\skills\UNDocsSearcher"
python -m pip install -r "$env:USERPROFILE\.codex\skills\UNDocsSearcher\requirements.txt"
& "$env:USERPROFILE\.codex\skills\UNDocsSearcher\run.ps1" doctor
```

## 使用

```powershell
$undocs = "$env:USERPROFILE\.codex\skills\UNDocsSearcher\run.ps1"
& $undocs search "charter" --collection un --limit 10 --out './unite.json'
& $undocs search "genocide" --collection ods --limit 10 --out './ods.json'
& $undocs fetch "A/RES/70/1" --pdf-out './ar701.pdf' --text-out './ar701.txt' --out './fetch.json'
```

## 边界

- `collection=un` 是 UNITE 网站索引，可能包含新闻；`collection=ods` 的关键词检索可能不完整。
- `fetch <symbol>` 依赖 ODS 文号存在且语言版本可访问；失败会保留错误，不伪造零结果。
- `total` 是服务端 `numberDocsFound`，不是已取全文数。

## 实测效果（2026-11-09）

以下命令与结果来自本机 `~/.codex/skills/UNDocsSearcher` 的实网运行；检索日期 2026-11-09（Asia/Shanghai），输出为该次运行实际返回的 JSON 报告。

```powershell
& .\run.ps1 search 'genocide' --collection ods --limit 5
```

- 状态：`ok`；服务端 `numberDocsFound`（即 `total`）= 1000；本次返回 5 条，`next_offset = 5`。
- 代表性结果（`result_type` 均为 `retrieved_metadata`，`provider` 为 UN Unite Search）：

| 题名 | 文号（symbol） | 链接 |
| --- | --- | --- |
| GENOCIDE FRANCE: DRAFT CONVENTION ON GENOCIDE | E/623/ADD.1 | https://documents.un.org/api/symbol/access?s=E%2F623%2FADD.1&l=E |
| GENOCIDE | E/RES/77(V) | https://documents.un.org/api/symbol/access?s=E%2FRES%2F77%28V%29&l=E |
| GENOCIDE | E/RES/153(VII) | https://documents.un.org/api/symbol/access?s=E%2FRES%2F153%28VII%29&l=E |
| GENOCIDE | E/RES/1420(XLVI) | https://documents.un.org/api/symbol/access?s=E%2FRES%2F1420%28XLVI%29&l=E |
| GENOCIDE | E/RES/117(VI) | https://documents.un.org/api/symbol/access?s=E%2FRES%2F117%28VI%29&l=E |

> 说明：`total = 1000` 是服务端 `numberDocsFound` 的命中总数，**不是**本次已取全文的文档数——本次只返回 5 条 ODS **元数据**（`content_scope`：ODS document metadata），正文需另用 `fetch <symbol>` 下载。`--collection ods` 只覆盖 ODS 文号检索，ODS 关键词检索本身可能不完整，`total` 也不等于 ODS 库内相关文献的全部数量；`collection=un` 还会混入网站/新闻记录。
