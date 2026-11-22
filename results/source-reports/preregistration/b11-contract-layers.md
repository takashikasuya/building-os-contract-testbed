# B11：契約検査のアブレーション（層 V0〜V2）の事前登録（#69）

この文書は、層ごとの判定し直しを**実行する前に** commit する。commit の後に、層の割当て、数え方、正常な入力の扱いを書き換えない。変えるときは新しい文書にし、結果を見た後であることを書く（その解析は探索的と呼ぶ）。

- 論文：bde-paper `f988200`。予備査読の指摘 1（契約の必要性と有効性）への追加実験 A の第 1 段。
- 元の事前登録：[`b2-contract-injection.md`](b2-contract-injection.md)（sha256 `e7c910d6…`）。注入、trace、S と C の述語は B3 のまま使う。
- 述語：`scripts/b3_lab/checks.py`（B3 の版。この解析では変えない）。契約試験一式 `bos-contract-suite-v0`、sha256 `ce211aa4…`。

## 1. 性格（先に書く）

- **注入はやり直さない。** B3 の 13 件の trace と、正常な入力の記録を、層に分けて判定し直すだけである（offline、L0）。live、image、承認は使わない。
- B3 の S と C の結果は、もう分かっている。そのため、この解析は**説明のための分解**であり、検出力についての新しい確証ではない。
- 結果を見た後の恣意を減らすため、層は**条件 id だけで機械的に**決める（§2）。どの注入をどの層で見つけたかは、割当てから計算で決まる。
- 下の §3 の「予想」は、B3 の既知の結果から引いたもので、実測ではない。

## 2. 層の割当て

層は累積である（V1 は V0 を含み、V2 は V1 を含む）。ある注入が層 Vk で「検出」とは、Vk に属する条件のどれかが、その trace に flag を立てることをいう（flag の数え方は B2 §3.2 と同じ：観測した拒否、または契約違反）。

| 層 | 条件（`checks.py` の id） | 主張の種類 | 必要な観測データ |
|---|---|---|---|
| V0 | S（`s_flags`：2xx でない応答、controlId の無い 202、TelemetryReading の必須項目と型） | 構造 | 北側の応答だけ |
| V1 | `pre-id-space` | 識別子空間 | 応答 ＋ 登録済みの Point id の一覧（twin）。ingress の注入では、送った frame の受付の結果 |
| V1 | `pre-write-permission` | 権限 | 要求の token の種類 ＋ 応答 |
| V1 | `fail-out-of-range-refused` | schema の範囲 | 要求の値 ＋ twin の ControlSchema ＋ 応答 |
| V1 | `t-invalid-release-value` | schema の enum（解除） | 要求の値 ＋ 応答 |
| V1 | `t-schema-missing` | schema の欠落（deny のとき） | 要求 ＋ twin の ControlSchema の有無 ＋ RI の policy |
| V2 | `post-origin-and-quality` | 時刻の出所・品質 | 行の `data`（時計のメタデータ） |
| V2 | `post-observation-time` | 観測時刻 | 送った frame の timestamp と、読んだ行の datetime |
| V2 | `fail-quality-refusable` | sim 時刻の巻戻り | 履歴（同じ Point の複数の行） |
| V2 | `post-readback` | 読戻し | 受付の後の読戻し（latest／history） |
| V2 | `post-default-readback` | 解除の後の priority の配列 | 機器の priority の配列と present value（南側の読取） |
| V2 | `post-actor-result-recorded` | 監査 | 監査の行数 |

- `post-observation-time` は Issue の表に無いが、時刻の主張なので V2 に置く。
- `checks.py` が出す条件 id で、上の表に無いものが出たら、解析は止め（Fail）、この文書を直さずに報告する。
- 目標の操作（`checks.TARGET`）に当たったか（targeted）も層ごとに数えるが、主な指標は「検出」である。

## 3. 入力と予想

| 入力 | 場所 | 注入 |
|---|---|---|
| telemetry（RI の部品、1 process） | `artifacts/b3-telemetry-injection-20261108b/traces.json` | T1、T2b、T3、T4、T5 |
| control の 5 run | manifest `b3-lab-px4-b-path.results.judged` の 5 つの path の `control/b3/results.json` の `traces` | T2a、T6〜T12 |

judged でない 3 つの run（manifest の `not_judged`）は使わない。trace が無い注入、Safety が RI の前で拒んだ trace は Not Tested（B2 §3.2）。

予想（B3 の既知の結果から。実測ではない）：

| 層 | 検出する注入 | 数 |
|---|---|---|
| V0 | T2a、T6、T7、T9、T11、T12 | 6 |
| V1 | ＋ T2b | 7 |
| V2 | ＋ T4、T5、T10 | 10 |
| どれでも検出しない | T1、T3、T8 | 3 |

## 4. 正常な入力の誤検出

B3 と同じ入力（PX4 A run 2、B run 1、計 163,394 件：書込 833、telemetry の行 162,559、解除 2）を、同じ単位で数える。B3 の `normal.py` の数え方を土台にする。

| 層 | 書込 | telemetry の行 | 解除 |
|---|---|---|---|
| V0 | `normal.py` の S | `normal.py` の S（`envelope_problems`） | `normal.py` の S（0） |
| V1 で足すもの | `fail-out-of-range-refused`：dispatch が ACCEPTED の書込の `final_value` が、run の `control/receipt.json` の `live_control_schema`（minValue〜maxValue）の外。`t-schema-missing`：`live_control_schema` が無い。`pre-write-permission`：writer の credential は Safety と OIDC にしか mount されない（receipt の `writer_secret_mounted_in`）ので、構成上 0。これは独立の測定ではないと書く | `pre-id-space`：行の `pointId` が、run の `ri-snapshot.json` の `points[].pointId` に無い | `t-invalid-release-value`：`release.jsonl` の release の `safety_decision.final_value` が 1 でない |
| V2 で足すもの | `normal.py` の C（transactions の不一致：監査、読戻し） | `normal.py` の C（`clock_problems`、巻戻り） | `normal.py` の C |

- 1 件は、その層のどれかの条件に当たれば 1 回だけ数える（重複を数えない）。
- 割合 = flag した件数 ÷ 判定した件数。判定した件数は B3 と同じ（Not Tested を除く）。
- ledger の sha256 が B3 の事前登録の値と違うときは止める（`normal.py` と同じ）。

## 5. 探索的な追加：Builder の SHACL と T8

- 問い：静的な意味モデルの検査（Builder の SHACL）は、T8／T9 の派生の twin（ControlSchema を外したもの）を検出するか。
- 入力：B3 の派生の twin（`artifacts/b3-lab-twins-approved-20261109`）と、承認済みの最終 RDF（`artifacts/b3-lab-rdf-approved-20261109`、対照）。
- 手順：Builder の版に入っている SHACL の shapes で、両方を検証し、`conforms` と違反の要約を記録する。shapes と Builder の SHA を記録する。
- **探索的**であり、V0〜V2 の数には入れない。Builder に shapes を当てる手段が手元に無いときは Not Tested と書く。

## 6. 受入

- この文書の commit が、層別の判定の results の生成より前にあること（`results.json` に、この文書の sha256 と commit を記録する）。
- `results.json`：Testbed の SHA、`checks.py` と解析の script の sha256、条件の割当て、層ごとの検出・targeted・誤検出、Not Tested の一覧。
- `docs/verification/` に記録し、manifest に `b11-contract-layers` を足す。
- Pass／Fail／Skip／Not Tested を分けて書く。ここでの Pass は「解析が事前登録どおりに走った」ことであり、層の予想が当たったことではない。予想と違った注入は、そのまま報告する。

## 7. 範囲外

- V3（B1 で gap だった検査）は、既存の 13 件では評価しない。#70（B12）で、別の事前に固定した注入の集合で扱う。
- 述語の改良、注入のやり直し、P1〜P5（tenant-portal）は扱わない。
