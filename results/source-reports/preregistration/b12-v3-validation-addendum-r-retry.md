# 事前登録の補遺：B12 の R1、R2 をもう 1 回だけ行う（2026-11-22、run の前）

[B12 の事前登録](b12-v3-validation.md) §6 への補遺である。**R1、R2 の 3 回目の run より前に commit する。**

- ユーザーの決定（2026-11-22）：「ソフトウェア契約の検証論文のために、再実施は必須ですか？必須ならやりましょう。」
  AI の答え：V3 の 4 つの条件のうち `fail-release-failure-reported` だけ、注入が 1 件も無い。V3 が 4 つの条件を検出する、と書くには必須。

## 1. 起きたこと

| 試行 | 日時 | 止まった所 | 書込 |
|---|---|---|---|
| 1 | 2026-11-21 | verify の引数の検査（`--release-inputs` を approved の run にしか許さない）、exit 2 | 無い |
| 2 | 2026-11-22 00:18Z〜00:27Z | 書込（15.0、Safety approved、RI 202、plant priority 8 = 15.0）の後、R の段の `c["plant"]["plant_container"]` が KeyError | 有る |

- 試行 1 は §6 の「環境の失敗（書込の前）」で、やり直しを 1 回使った（試行 2）。
- 試行 2 は §6 の「書込の後の失敗」で、**やり直さず Not Tested** と記録した（`docs/verification/2026-11-21-b12-v3-validation.md`）。この記録は書き換えない。
- 試行 2 の原因は Testbed の欠陥である。`scripts/e2e03_lab/plant.py` の `require_owned_plant` が、R の段が使う `plant_container` を verify に渡していなかった。
  R の段（connector を外す、plant を pause する、解除する）は、どちらの試行でも一度も実行されていない。注入の結果は何も出ていない。

## 2. 変えること

1. R1、R2 を、新しい stack と plant で **1 回ずつだけ** もう一度行う（試行 3、D=20261122b）。順番は R1、R2。
2. 修正：9e6b540（`plant_container` を渡す）。R の段を verify と同じ context の key で通す試験を足した
   （`tests/test_b3_control_run.py::test_r_release_step_runs_end_to_end_with_the_verify_context`、修正を外すと Fail する）。
3. 試行 3 が、また Testbed の欠陥で止まったときは、やり直さず Not Tested とする。

## 3. 変えないこと

- 注入の中身（15.0 を書き、R1 は connector を plant の network から外して、R2 は plant を `docker pause` して解除）、判定（`v3.py` 71209b9）、
  承認（2026-11-21、鮮度 2026-11-22T13:46:27Z、run.sh は 13:06:27Z を過ぎると始めない）、Safety の材料、hard limit、twin、plant の image。
- S1〜S3 と telemetry の注入の結果。

## 4. 限界

- 書込の後の失敗をやり直すので、§6 の文言から外れる。外れる理由は、失敗が注入の前の Testbed の欠陥で、注入の結果を見ていないからである。
  論文には、試行 1〜3 をすべて書く。
