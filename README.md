# 分水 BUNSUI

整数の水を、配管を組んでタンクへ。**整除・同着・仮説**の三本柱でできた離散フロー・パズル。全15図。

依存ゼロの単一HTMLで動きます。`dist/bunsui.html` をブラウザで開くだけ。サーバー不要、オフライン可。

## 遊び方

水源（緑）から出る整数単位の水を、パイプを回して各タンクへぴったり届ける。

- パイプはクリックで90°回転。直管 I・曲管 L・三方管 T・十字管 X の4種。
- 水は1ティックに1マス進む。分岐に入ると出口の数で**均等に割れる**——割り切れなければ破裂。
- 合流が成立するのは、複数の水が**同じティックに同じ部品へ着いたとき**だけ（同着の掟）。経路長 = 到着時刻。
- すべてのタンクを要求量ぴったりで満たし、盤上に水を残さなければ合格。
- 操作: <kbd>Space</kbd> 通水/停止　<kbd>S</kbd> 一歩　<kbd>R</kbd> 水を抜く

ルールの全文はゲーム内「水の掟」と [`docs/design.md`](docs/design.md) を参照。

## 開発

レベル定義（Python）を正典とし、ビルドで `levels.json` とゲーム本体を生成します。エンジンは Python と JS の二実装があり、ビルド時に同一データで両者が一致することをテストで保証しています。

```bash
# 1) レベルを検証し、データとゲーム本体を生成
python tools/build.py        # -> src/levels.json, tests/solutions.json, dist/bunsui.html

# 2) テスト（CIと同じ）
python tests/test_engine.py  # Python エンジンで全15図を検証
node   tests/run_tests.js    # JS エンジンで全解を再生・初期未解を確認
```

ビルドに失敗した解やスクランブルがあると、生成前に中断します。手計算でのティック検証は行いません——エンジンが正典です。

## 構造

```
src/
  template.html   ゲームUI。__ENGINE__ と __LEVELS__ を含む雛形
  engine.js       離散フローエンジン（正典・ブラウザ用、ビルドで注入）
  levels.json     全15図の盤面データ（生成物。手で編集しない）
tools/
  build.py        検証 → JSON生成 → 単一HTML組み立て
  engine.py       エンジンの Python ミラー（レベル設計・検証用）
  levels_1_5.py   図1〜5の定義と正解
  levels_6_15.py  図6〜15の定義・正解・scramble()
tests/
  run_tests.js    JS エンジンの全解検証
  test_engine.py  Python エンジンの全解検証
  solutions.json  全正解の回転値（生成物）
docs/
  design.md       設計記録（ルール仕様・三本柱・全図の記録・ロードマップ）
  HANDOFF.md      Claude Code 向け引き継ぎ
dist/
  bunsui.html     配布用単一ファイル（生成物）
```

## レベルを追加するには

`tools/levels_6_15.py` に倣って盤面 `LXX` と正解 `SXX` を定義し、`NEW` に追加して `tools/build.py` を実行。検証が通れば自動で全成果物に反映されます。詳しい数理（パリティ法則・整除カタログ）は [`docs/design.md`](docs/design.md)。

## ライセンス

MIT License. See [LICENSE](LICENSE).
