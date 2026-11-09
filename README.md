# UNDocsSearcher 部署指引

独立检索联合国文件（UNITE/ODS），并可按文号下载 PDF。主要访问 `search.un.org` 与 `documents.un.org`。

仓库：<https://github.com/HuiwowICCSkills/UNDocsSearcher>（私有）。

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
