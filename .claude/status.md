---
name: 稼働状況
description: プロジェクトの稼働状況と、停止した経緯
type: project
---

## 現在: 停止中（2026年9月13日〜）

**Supabase の無料枠を別の用途に使いたくなったため、Supabase を止めた。**
それに伴いプロジェクト全体を停止した。

### 止めたもの

- GitHub Actions の `Update Monitor`（毎時実行）を `gh workflow disable` で無効化
  - 止める前は毎回5〜9分かけて失敗し続けていた（Supabaseが無いため）
  - Actions の実行時間を無駄に消費し、失敗通知も出ていた

### 残してあるもの

- **GitHub Pages はそのまま公開中** → https://torunishijima.github.io/mideast-monitor/
  - `main` の `/docs` から配信。2026年4月15日時点のレポートが読める状態で凍結
  - `pages-build-deployment` ワークフローは active のままだが、`/docs` に
    変更があったときだけ動くので、放っておいても実行されない
- リポジトリは public のまま
- `.github/workflows/update.yml` の `cron: '0 * * * *'` もそのまま

### 再開するとき

```bash
gh workflow enable "Update Monitor"
```

ただし**Supabaseの再設定が先**。`supabase_store.py` と `config.py` が
参照している接続情報を作り直す必要がある。

再開の前に、そもそもSupabaseを使い続けるかを考え直してもよい。
履歴の保存が主目的なら、`history_store.py` の仕組みを使って
リポジトリ内のファイルに持たせる選択肢もある（データ量次第）。
