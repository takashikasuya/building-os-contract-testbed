# 事前登録の補遺：PX4 段 2 の B の live と、比べる相手の offline の初期状態（2026-11-12）

[段 2 の事前登録](px4-stage2.md) §4 と §5 の問い 2 への補遺である。

- **live の run より前に commit する。** この時点で、段 2 の live の run（A も B も）は 1 回も走らせていない。offline の 5 窓（問い 3）の結果は見た後である。
- ユーザーの決定（2026-11-12、推奨の案）：下の §2。

## 1. 問題

- 段 2 の offline の B は、PX1 の config の開始（7 月 15 日 0 時）から 9 日と 13 時間を、書込なしで進めてから窓に入った（`stage2_offline.py`、`b_warmup_s`）。
- live の Active は 1 倍速の壁時計でしか動かない（production の DeploymentSpec は SimClock を許さない）。そのため、live の B では、9 日の warmup を同じように進められない。
- 問い 2 は「live の KPI が、同じ窓の offline の KPI と許容差の中で一致するか」を問う。初期状態が違えば、差は経路ではなく初期状態から来る。
- A（BOPTEST）には、この問題が無い。BOPTEST の `/initialize` の `warmup_period`（7 日）を、live でも offline でも同じように使えるからである。

## 2. 案

1. **B の live の plant の config は、開始を 7 月 24 日の現地 13:00 にする**（`scripts/px1_lab/plant_config.py --start 2019-07-24T13:00:00-07:00`）。
   - 他は段 2 の B の config（`px1-plant-config-20261104b`）と同じ。違うのは開始の時刻だけである。
   - plant は、hvac-sim の初期状態（室温 24 ℃）から 1 倍速で動く。
2. Active は、今の lab と同じく、control-service を起動した時点から 8 周期（2 h）回す。
   - 最初の周期の sim 時刻（開始からの秒）を、live の記録から読む。
3. **問い 2 の「同じ窓の offline」は、live と同じ config で、同じ時刻から回し直した offline とする。**
   - `px1_closedloop.py --config-dir <live の config> --warmup-s <live の最初の周期の sim 時刻> --duration-s 7200`
   - policy と model は live と同じ（その場の MPC、移した MPC）。
4. 問い 3 の 5 窓の offline（9 日の warmup）は、そのまま報告する。問い 2 の比較には使わない。
5. A は変えない。live は `start_time` を 7 月 24 日 13:00、`warmup_period` を 7 日にする。比べる相手は段 2 の offline の 7/24 の run である。

## 3. 理由

- 問い 2 の目的は、経路（BOS と Safety）を通しても、ハーネスと同じ結果になることを示すことである。そのためには、初期状態をそろえるのがいちばん直接的である。
- 1 倍速で 9 日の warmup を回すのは、現実的でない。
- live の B の plant は、hvac-sim の初期状態から始まる。窓の初めは過渡になるが、live と offline の両方に同じように効く。

## 4. 変えないこと

- 許容差（エネルギー ±5 %、不快度 ±0.5 K·h）、問い 1、止める条件、承認（日ごと、鮮度 24 h）。

## 5. 決めた後に作ったもの（2026-11-12）

- live の plant の config：`artifacts/px4-s2-b-plant-config-live-20261112`（`config.yaml` `a30341bc…`）。
  - 段 1 の B の config（`px4-b-plant-config-20261107`）との違いは、`start_datetime`（7/15 0:00 → 7/24 13:00、-07:00）と、`clock.ttl` のコメントだけである。
  - 問い 2 の offline の回し直しも、この config を使う。
- live の policy は、段 2 の offline と同じ PolicySpec のファイルをそのまま署名する。
  - その場の MPC：`px4-s2-b-insitu-mpc`。
  - 移した MPC：`px4-s2-b-transferred-from-a-mpc`。bundle には `transfer_mapping`（`px4-xfer-a-to-b`）も載せる（ADR-0017 D6）。
  - Deployment の draft の `policy` も、この id にした。
