# PX4 段 2：B の live（その場の MPC、移した MPC）（2026-11-21）

- 事前登録：`docs/preregistration/px4-stage2.md` §2、§4、§5。補遺：`px4-stage2-addendum-live-b-window.md`（初期状態と窓、run の前）、
  `px4-stage2-addendum-ri-runtime.md`（RI の実行用の image、3d8b1f8、run の前）
- 承認：human:<approver>（TTY）2026-11-21T13:46:43Z〜14:13:00Z（`manifest.yaml` `live_day_20261121.px4_s2_b`）。AI は承認していない
- 経路：hvac-sim plant（`artifacts/px4-s2-b-plant-config-live-20261112`、開始 7 月 24 日 13:00 現地）→ Nexus → RI `8c87146`
  （runtime `f3b93cdf…`）→ BDE `d46958f` の Safety。BDE の書込は priority 8、max_slew 2.0
- 問い 2 の比較：`scripts/px4_lab/stage2_live_b.py`（cecea8e、826a9d4、482fffe。KPI を出す前に固定）。live の呼び出しは無い

## 結果のまとめ

| 問い | B その場（insitu） | B 移した（transferred） | A その場 / A 移した |
|---|---|---|---|
| 1 Safety の違反 0 | **Pass** | **Pass** | Not Tested |
| 2 offline と一致 | **Pass** | **Pass** | Not Tested |

事前登録の問い 1、2 は「4 回とも」なので、**問い 1、2 の全体は Not Tested（4 回のうち 2 回）** である。B の 2 回は条件を満たした。
A の live は、pin した BOPTEST の proxy の image（`5de47356…`）が daemon に無く、Docker Desktop が registry に出られないため、走らせていない。

## run

| | insitu | transferred |
|---|---|---|
| run（verify） | `artifacts/px4-s2-b-insitu-run-20261121`（results `16d3c973…`） | `artifacts/px4-s2-b-transferred-run-20261121`（results `756da728…`） |
| plant | `artifacts/px4-s2-b-insitu-plant-20261121` | `artifacts/px4-s2-b-transferred-plant-20261121` |
| control-service | 16:52:14Z〜18:52:04Z | 19:57:28Z〜21:57:25Z |
| release の後の読み | 19:08:39Z | 22:14:01Z |
| verify の数 | Pass 194 / Fail 4 / Skip 0 | Pass 197 / Fail 4 / Skip 0 |

## 問い 1（Safety の判定の外の書込 0、範囲と max_slew の違反 0、止めた後の dispatch 0）

両方の run で、次の verify の検査が Pass である。

- `active_every_proposal_inside_action_range`、`active_final_values_respect_max_slew`
- `active_audit_row_per_write_by_the_safety_writer`、`active_safety_ledger_production_entry_per_write`、`active_connector_wrote_priority_8`
- `active_no_dispatch_after_control_service_stop`、`active_cycles_match_the_plan`、`active_no_fallback`
- bundle の検査（署名、改ざんした model / 移転の対応付けの拒否、信頼しない署名者の拒否、鍵を書かない）。transferred は移転の対応付けの検査も Pass

### verify の Fail（両方の run で同じ 4 件。問い 1 の条件ではない）

- `release_slot_8_held_the_last_active_value`：**Testbed の検査の欠陥。** control-service を止める約 1 s 前に、9 回目の周期の書込が
  Safety の承認を経て入った（insitu 18:52:03.67Z の 23.7963、stop 18:52:04Z。transferred 21:57:24.83Z の 24.1995、stop 21:57:25.81Z）。
  ledger は 9 件、audit と relay は各 10 行（9 回の control と release）、止めた後の ledger は 0 件。検査は summary の 8 周期の最後の値（insitu 23.7803、transferred
  24.2104）と比べるので外れる。9 回目も Safety の判定の中の書込で、止めた後ではない。release の後の配列は空で、present value は
  relinquishDefault（transferred の `priority-end.json`：全部 null、24.0）。
- `real_core_s3_history_preserves_utc_values_data`、`real_core_s3_history_one_row_per_id`：RI #657（cold reader が id で重複を除かない）。B3 / PX4 段 1 / B13 と同じ。
- `execution`：上の Fail を受けたもの。

## 問い 2（live と、同じ config・同じ時刻の offline の KPI）

窓の規則（補遺 live-b-window §2 の 2〜3 を実装に落としたもの。insitu の run の後、KPI を出す前に固定、826a9d4）：

- T0 = plant が監査した最初の control の書込の時刻以前の、最後の plant の tick の sim 時刻。窓は (T0, T0 + 7200] s。
- これで、live の最初の書込が効く tick と、offline の `--warmup-s T0` の最初の書込が効く tick がそろう。
- 両方の run で T0 = 240 s、窓 [240, 7440]。E2E-04 の active_window（1 tick 後、[300, 7500]）は感度として出す。判定しない。
- 採点は、両方とも `px1_closedloop.kpi` の規則（t の行は直前の dt を表す、dt 60 s、帯 22〜24 ℃）。

| | insitu | transferred |
|---|---|---|
| live のエネルギー（kWh） | 1.7374523 | 1.6576542 |
| offline のエネルギー（kWh） | 1.7374523 | 1.6576541 |
| 相対差（許容 5 %） | 2.5e-8 | 3.3e-8 |
| live の不快度（K·h） | 0.0 | 0.3717 |
| offline の不快度（K·h） | 0.0 | 0.3687 |
| 差（許容 0.5 K·h） | 0.0 | 0.0031 |
| same_setup（帯、config sha、dt） | all true | all true |
| **判定** | **Pass** | **Pass** |
| 判定の成果物 | `artifacts/px4-s2-b-q2-insitu-20261121`（`32d051e1…`） | `artifacts/px4-s2-b-q2-transferred-20261121`（`5566932c…`） |
| offline | `artifacts/px4-s2-b-q2-offline-insitu-20261121`（record `4dea2b16…`） | `artifacts/px4-s2-b-q2-offline-transferred-20261121`（record `714427b4…`） |
| Oracle の export | `oracle-export-s2binsitu.csv`（`d8bc7e3f…`） | `oracle-export-s2btransferred.csv`（`5e623c32…`） |

### 記録（判定しない）

| | insitu | transferred |
|---|---|---|
| E2E-04 の台形（同じ窓）エネルギー / 不快度 | 1.73694 kWh / 0.0044 K·h | 1.65740 kWh / 0.3752 K·h |
| E2E-04 の窓 [300, 7500] エネルギー / 不快度 | 1.73228 kWh / 0.0 K·h | 1.65856 kWh / 0.3692 K·h |

- 報告だけの比（事前登録 §5、B の live の 1 窓）：R_E = 1.6577 / 1.7375 = 0.954、不快度の差 +0.37 K·h（移した − その場）。
  1 窓だけなので CI は出さない。問い 3 の比は offline の 5 窓で出す（`2026-11-12-px4-stage2-offline.md`）。

## 制限

- 問い 1、2 は A の 2 回が Not Tested。A は proxy の image を作り直してから、新しい承認の日に行う。
- RI の dotnet runtime の image が段 1 の B と違う（補遺 ri-runtime）。問い 2 の相手は offline なので、この違いは入らない。
- live の plant は hvac-sim の初期状態（室温 24 ℃）から始まる（補遺 live-b-window §3）。窓の初めは過渡で、live と offline の両方に同じように効く。
- 窓の規則（T0 の取り方）は、insitu の run が終わった後、KPI を出す前に決めた。E2E-04 の窓での live の値も上に出した。
  それを offline（[240, 7440]）と比べても、エネルギーの差は insitu 0.3 %、transferred 0.05 %、不快度の差は 0.0 / 0.0005 K·h で、許容差の中である（窓がずれた比較なので参考）。
- `release_slot_8_held_the_last_active_value` の欠陥は、Testbed の verify の側で直す（#72。summary ではなく ledger の最後の書込と比べる）。この run の結果は書き換えない。
