# B11：契約検査のアブレーション（層 V0〜V2）の結果（#69）

**offline の判定し直しだけ。注入はやり直していない。live、image、承認は使っていない（`images_executed: []`、live の呼出し 0）。**

- 事前登録：[`b11-contract-layers.md`](../preregistration/b11-contract-layers.md)（commit `5111a71`、sha256 `e3cf4763…`）。判定の script（`675203b`）より前に commit した。
- 述語：`scripts/b3_lab/checks.py`（B3 の版のまま）。契約試験一式 `bos-contract-suite-v0`（`ce211aa4…`）。
- 結果：`artifacts/b11-contract-layers-20261121/results.json`（sha256 `0d99a1b2…`、Testbed `675203b`、作業木はきれい）。
- 性格：B3 の既知の結果を、条件 id で決めた層に分けたもの。説明のための分解であり、新しい確証ではない。

## 判定

| 項目 | 結果 |
|---|---|
| 解析が事前登録どおりに走った（層の無い条件 id は 0） | Pass |
| 層ごとの検出が、事前登録の予想と一致 | 一致（V0 6、V1 7、V2 10） |
| 正常な入力の誤検出（事前登録の規則） | V0 0、V1 161、V2 161（／163,394）。161 は規則の誤り（下記） |
| Builder の SHACL で T8 の twin（探索的） | Not Tested（静的な観察だけ） |
| Not Tested の注入 | 0 |

## 層ごとの検出（13 件）

| 注入 | 最初に検出した層 | V1 の条件 | V2 で足した条件 |
|---|---|---|---|
| T2a 識別子の別の綴りで読む | V0（403） | `pre-id-space` | — |
| T6 下限より下 | V0（400） | `fail-out-of-range-refused` | — |
| T7 読取の token で書く | V0（403） | `pre-write-permission` | — |
| T9 schema を外す（deny） | V0 | `t-schema-missing` | — |
| T11 解除に 0 | V0 | `t-invalid-release-value` | — |
| T12 gateway を止めて解除 | V0（503） | — | `post-default-readback` |
| T2b 別の綴りの frame | **V1** | `pre-id-space` | — |
| T4 時計のメタデータを除く | **V2** | — | `post-origin-and-quality` |
| T5 sim 時刻の巻戻り | **V2** | — | `fail-quality-refusable` |
| T10 機器が丸めて適用 | **V2** | — | `post-readback` |
| T1 単位（K） | 検出なし | — | — |
| T3 値の無い frame | 検出なし | — | — |
| T8 schema を外す（allow） | 検出なし | — | — |

- 目標の操作に当たった数（targeted）は、V0 0、V1 6、V2 10。V0 の 6 件は拒否を観測しただけで、どの契約に当たるかは名指せない。
- 必要な観測データ：
  - V0 は北側の応答だけで済む。
  - V1 は、登録済みの id の一覧、token の種類、twin の ControlSchema が要る。
  - V2 は、行の `data`、履歴、読戻し、南側の priority の配列、監査の行数が要る。T12 の `post-default-readback` は、機器の priority の配列（南側）を読まないと出ない。
- 検出できなかった 3 件（T1、T3、T8）は、B1 で gap か conflict だった条件である（単位、欠測を 0 で埋めない、検証できないときの拒否）。#70（B12）の V3 が対象にする。

## 正常な入力の誤検出

| 層 | 事前登録の規則 | 内訳 |
|---|---|---|
| V0 | 0 / 163,394 | — |
| V1 | 161 / 163,394 | PX4 A の書込 161 件すべてが `fail-out-of-range-refused` |
| V2 | 161 / 163,394 | V1 と同じ。B3 の C（監査、読戻し、時計、巻戻り）は 0 |

**161 は Testbed の規則の誤りであり、RI や Safety の振る舞いではない。**

- 事前登録 §4 は、Safety の `final_value` を RI の `live_control_schema` と比べた。
- PX4 A では、Safety は ℃（hard limit [21, 27]）で、RI の ControlSchema は K（294.15〜300.15）である。単位の違う値を比べたので、すべての書込が範囲外になった。
- PX4 B は両方 ℃ で、0 / 672 だった。

探索的な数え直し（結果を見た後に書いた。事前登録の数は置き換えない）：

- RI の監査の行（id = controlId）の `request.value` を、RI の ControlSchema と比べた。
- 結果は、範囲外 0 / 833（A 0 / 161、B 0 / 672）、監査の行が無い書込は 0。
- `artifacts/b11-exploratory-ri-value-20261121/results.json`（sha256 `b5a5b2a8…`、script `scripts/b11_lab/exploratory_ri_value.py`）。

その他の V1 の条件：

- `pre-id-space`：telemetry の行の Point id は、すべて ri-snapshot に登録されていた（0 / 162,559）。
- `t-invalid-release-value`：解除の 2 件は、どちらも値 1（0 / 2）。
- `pre-write-permission`：writer の credential は `ri-oidc` と `safety-runtime` にしか mount されないので、構成上 0 である。独立の測定ではない。

## 探索的：Builder の SHACL と T8（Not Tested）

- Builder `f2f313e` の SHACL の検証は TypeScript（`rdf-validate-shacl`）で動く。手元の worktree に `node_modules` が無く、network からも入れていないので、走らせていない。
- 静的な観察として、`schema/building_model.shacl.ttl`（sha256 `3cf6237c…`）の `sh:path` は、`brick:` 12、`rec:` 375、`sbco:` 45 だけだった。T8／T9 が外す `bos:dataType`、`bos:minValue`、`bos:maxValue` への制約は無い。
- そのため、走らせても、この shapes は T8 の twin を違反として出せない見込みである。これは実行の結果ではない。

## 試験

- `tests/test_b11_layers.py`（8 件）と `tests/test_b3_checks.py`：27 Pass。
- `checks.py` が出しうる条件 id と、層の割当てが一致することを試験で確かめている。

## 限界

- 注入の集合は B3 のもので、作者が設計した。13 件の検出の数は、V3 の性能の主張には使わない（#70）。
- 層の境は、`checks.py` の条件 id で機械的に決めた。別の分け方（例：権限を構造に入れる）では数が変わる。
- 事前登録の誤検出の規則に、単位の誤りがあった。次の事前登録（B12）では、比べる値を RI が受け付けた値に固定する。

## Rollback

- 追加したのは、文書、script、試験、artifacts、manifest の `b11_layers` だけ。製品と既存の結果には触れていない。この branch を捨てれば元に戻る。
