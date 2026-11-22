# 事前登録の補遺：PX4 段 2 の BDE の pin と、offline の BOPTEST の点の名前（2026-11-12）

[段 2 の事前登録](px4-stage2.md)（sha256 `8d77a040…`）への補遺である。

- **段 2 の run より前に commit する。** この時点で、段 2 の run（offline の閉ループも live も）は 1 回も走らせていない。pin の前の確認 2 は、評価の 5 日とは別の窓（BDE の既定の窓）で回した。
- ユーザーの決定（2026-11-12、推奨の案）：下の 2 つ。

## 1. BDE の pin：`d46958f` に確定する（§8-6）

- §8-6 の 2 つの確認は、どちらも Pass だった（記録 (`../verification/2026-11-10-px4-stage2-bde-pin-check.md`, not exported)、manifest の `px4-stage2-bde-pin-check`）。
  - 確認 1：重み 0.3 の A と B の ControlSpec が、2 つの版で byte で同じだった。
  - 確認 2：閉ループのハーネスの結果が、2 つの版で同じだった。B は byte で同じ。A は 96 周の timeline が同じで、KPI も `time_rat` 以外は同じ。
- そのため、段 2 の offline も live も、BDE `d46958f`（build `artifacts/bde-d46958f-20261110`）で行う。移転の build（`transfer_recheck_928`）と同じ版である。
- casadi は、段 1 と同じ `artifacts/boptest-candidates-20261027/deps`（3.8.2）から読む。

## 2. offline の BOPTEST：ControlSpec の点を、harness の写しで信号名に直す（§4 offline）

- 事前登録 §4 の offline は、BOPTEST で BDE の `bde_testbed.boptest.closedloop` を使うとしている。
- §3 の ControlSpec（生成器の `--transfer-vars`）は、点を `fixtures.BASE` + BOPTEST の信号名の IRI で持つ。一方、closedloop は、`/advance` の応答を信号名で読む。そのまま渡すと、最初の周で KeyError になる（確認 2 の attempt 2 で、両方の版に起きた）。
- 決定：`scripts/px4_lab/boptest_closedloop.py --local-points` で回す。
  - harness 用の写し（`control.local-points.yaml`）で、`point` と `feedback_points` の値から prefix だけを外す。
  - id、帯、罰、範囲、rate_limit は変えない。写しの sha256 は、run ごとの `record.json` に元の sha256 と並べて残す。
  - ControlSpec そのもの（§3 の生成器の出力）は手で書き換えない。この方針は変わらない。
- 同じ wrapper で、BDE の `rest.KEY` は Testbed の plant の run の鍵に、`rest.IMAGE` は pin した BOPTEST の web の image（`2a1f0eda…`、curl 入り）に替える。
  - plant は `scripts/boptest_plant.py up --no-proxy` で起動し、harness だけが時間を進める。
  - 理由：BDE の proxy の image（`5de47356…`）が daemon から消えていて、作り直せない。
- PX1（B）の `scripts/px4_lab/px1_closedloop.py` と live の経路は変えない。

## 3. 変えないこと

- 評価の 5 日、窓（13:00〜15:00）、方式、指標と判定（§5）、止める条件（§6）、許容差（§8-2）、規則の baseline（§8-3）。
- 移転の対応付けの宣言（§8-5）は、2026-11-10T09:36Z に人が TTY で済ませている（`artifacts/px4-transfer-declaration-20261110`、manifest の `transfer_declaration`）。
  - 訂正（2026-11-12、段 2 の run の前）：この補遺の最初の版は「承認を待っている」と誤って書いていた。
