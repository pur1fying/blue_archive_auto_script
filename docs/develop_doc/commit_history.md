# 脚本更新历史

WebUI 通过已有的认证 `/ws/trigger` 通道调用 `get_commit_history`。参数为
`channel`（`stable` / `dev`，默认使用当前配置）、`limit`（1–500，默认 100）和
`refresh`（布尔值）。它不提供匿名 HTTP 接口，也不修改更新渠道或 Mirror CDK。

历史来源按更新渠道隔离：稳定版为 `pur1fying/blue_archive_auto_script`，开发版为
`Kiramei/baas-dev`，均查询 `master`。首先使用有效期十分钟的元数据缓存，然后查询
GitHub 的提交列表 API。每项只保留完整 Hash、作者名、提交信息首行；不请求单次提交的
文件详情，也不保存邮件地址、提交正文、树对象或 diff。界面可截取 Hash 前六位显示。

缓存位于 `config/commit-history/{channel}.json`，最多 500 项、2 MiB，原子替换。
网络失败时依次使用同渠道的缓存、匹配来源且位于 `master` 的本地 Git 历史，以及
安装包根目录的 `.baas-commit-history.json`。响应的 `source`、`stale`、`partial` 和
`issue` 反映数据来源及可用性；部分分页失败仍保留已取得的行。缓存不是 Git 对象库，
此功能不会执行 fetch、deepen、unshallow、checkout 或任何安装更新操作。

Mirror 仓库快照工作流在删除 `.git` 之前运行：

```sh
python3 develop_tools/package_commit_history.py --repository pur1fying/blue_archive_auto_script
```

它生成以下格式的轻量清单，清单随仓库快照一起分发：

```json
{
  "schema": 1,
  "repository": "pur1fying/blue_archive_auto_script",
  "reference": "master",
  "entries": [
    {"hash": "0123456789abcdef0123456789abcdef01234567", "author": "Example", "message": "Example subject"}
  ]
}
```

CI 的浅克隆通过 GitHub 元数据 API 补齐记录，后续分页固定到当前打包提交，不下载旧
Git 对象。可选 `GITHUB_TOKEN` 只用于此 CI 请求，不写入清单或日志；API 不可用时可保留
当前已有的本地记录。没有 Mirror 开发版下载地址或 CDK 验证失败均不影响 GitHub、Git、
缓存这些历史来源。已有的旧镜像若未携带清单，且本地无 Git、无缓存、无网络，界面只能
说明记录不可用；不会为此下载完整仓库，也不会把历史元数据视作安装包真实性证明。
