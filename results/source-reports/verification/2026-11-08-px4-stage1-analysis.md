# PX4 段 1：学習、罰の重みの replay、移転の検査（offline、2026-11-08）

[事前登録](../preregistration/px4-stage1.md) §2 の手順 4〜6 の記録。手順 5 の具体は、結果を見る前に固定した [補遺](../preregistration/px4-stage1-addendum-replay.md)（sha256 `7ce2e685…`、commit `e30d1a2`）に従う。入力は 励起の記録 (`2026-11-08-px4-stage1-excitation.md`, not exported) の A run 2 と B run 1。段 1 は探索的で、合否は決めない。

image は実行していない。BOPTEST、plant、BOS、Oracle は読んでいない。BDE は `5f36355`（`artifacts/bde-5f36355-20261107`）。

## 結論

- **事前登録 §3 の基準を満たす重みは無い。** B は 0.3 以上で内側の割合 1.0、A は最大 0.29。§3 のとおり、**段 2 には進まず、目的を見直す**。
- A の失敗は重みの問題ではない。A の model は、設定値に対する室温の利得が小さい（定常で 0.17 K/K、B は 0.59 K/K）。MPC は、罰が小さいと電力を取って 27 ℃に、大きいと帯に入れるために 21 ℃に張り付く（下の「探索」）。
- **移転の検査は、両方の向きとも拒否された。** 原因は BDE の点の照合（BDE #928）。model や範囲の問題ではない。
- **段 1b（在室の時間帯だけで学習、探索的）では、基準を満たす最も小さい重みは 0.1。** A の利得は 0.69 K/K、B は 0.93 K/K になった。ただし、A は 0.1 では快適性の罰がほぼ効かない（下の「段 1b」）。

## 手順 4：学習（`run_bde_pipeline.py`）

dataset の窓を、事前登録の窓 [励起の開始, 開始 + 期間] で切るように直した（`score_window`。期間は manifest の `scenario.duration_s`）。最初の実行（`artifacts/px4-{a,b}-train-20261108`）は、窓が励起の後の release と既定の制御（B は約 1.75 日、A は約 7 h）まで含んでいたので、使わない。

| | A（`artifacts/px4-a-train-20261108b`） | B（`artifacts/px4-b-train-20261108b`） |
|---|---|---|
| sim の窓 | 2026-07-14T15:25Z〜07-16T15:25Z（P2D） | 2019-07-15T08:20Z〜07-22T08:20Z（P7D） |
| 行（学習／holdout） | 576（432／144） | 2016（1440／576） |
| 軸で落ちた行 | `changed` 70、窓の外 2500 | `changed` 110、窓の外 2495、clock の外の command 1 |
| model | `linear_ssm`。state は室温、冷房とファンの電力、action は `zone_cooling_setpoint`、外生は外気（A と B で同じ） | 同じ |
| holdout の 1 歩（15 分先）の RMSE | 室温 0.301 K、冷房 0.169 kW、ファン 0.032 kW（141 行） | 室温 0.585 K、冷房 0.146 kW、ファン 0.011 kW（573 行） |
| BDE の評価（参考） | `rmse_1step` 0.178、`rmse_16step` 0.569 | 0.386、0.941 |
| results.json | 11 Pass／1 Fail（`fecc2d4d…`） | 11 Pass／1 Fail（`ad242d8b…`） |

- Fail の 1 件は `source_run_passed` で、どちらも元の run の 1 Fail（RI #657、cold tier の重複）による。BDE の経路（parquet mode）には重複が無いことを確かめてある（励起の記録 (`2026-11-08-px4-stage1-excitation.md`, not exported)）。判定は変えない。
- A の学習には、最初の約 7.75 sim h（Safety が拒否し、plant の既定の 30 ℃だった区間）が入っている。action の値は 21〜30 ℃。

## 手順 5：罰の重みの replay（補遺の手順）

`scripts/px4_lab/weight_replay.py`。holdout の制御周期ごとの state から、学習した model と `LinearMPCPolicy` で 16 周期（4 h）回した。

- 重みの ControlSpec は、帯の制約の penalty だけを置き換えて作った。
- A では、生成器（`prepare_excitation_approval_inputs.py --comfort-penalty`、`artifacts/px4-weight-generated-20261108`）の出力と、description 以外が 4 つとも同じだった。生成器で作り直した 0.1 は、承認済みの ControlSpec と byte で同じ。

「内側」は 16 周期目の提案が 21.1 < u < 26.9 にあること。「帯の外」は model が予測した室温の、22〜24 ℃の外の量（K·h／4 h）の平均。

| 重み | A：内側（16 周期目） | A：内側（1 周期目） | A：16 周期目の中央値 | A：帯の外 | B：内側（16 周期目） | B：内側（1 周期目） | B：16 周期目の中央値 | B：帯の外 |
|---|---|---|---|---|---|---|---|---|
| 0.03 | 0.000 | 1.000 | 27.0 | 2.45 | 0.234 | 0.849 | 27.0 | 3.91 |
| 0.1 | 0.000 | 1.000 | 27.0 | 2.45 | 0.266 | 0.859 | 27.0 | 3.80 |
| 0.3 | 0.292 | 0.938 | 21.0 | 1.25 | **1.000** | 1.000 | 23.85 | 0.99 |
| 1.0 | 0.271 | 0.792 | 21.0 | 1.23 | **1.000** | 1.000 | 23.95 | 0.99 |

開始の state は A が 48、B が 192。記録は `artifacts/px4-a-weight-replay-20261108/replay.json`（`c048230e…`）と `artifacts/px4-b-weight-replay-20261108/replay.json`（`eb704427…`）。各開始の提案と予測は `rollouts.json` にある。

**§3 の判定：当てはまる重みは無い。** B だけなら 0.3 になる。

### 探索（結果を見た後。判定は変えない）

学習した model の定常値。外気は holdout の中央値（A 23.2 ℃、B 23.4 ℃）。

| 設定値 | A の室温 | A の冷房 | B の室温 | B の冷房 |
|---|---|---|---|---|
| 21 ℃ | 23.93 | 0.425 kW | 22.00 | 0.901 kW |
| 24 ℃ | 24.43 | 0.377 kW | 23.77 | 0.647 kW |
| 27 ℃ | 24.94 | 0.328 kW | 25.54 | 0.392 kW |

- A の model では、設定値を 21 ℃まで下げても、室温は帯の上端 24 ℃の近くにとどまる。帯に入れる手段が下限しかないので、罰が電力に勝つと 21 ℃に張り付く。
- 原因の候補は 2 つあり、どちらも確かめていない。
  1. bestest_air の FCU が在室の時間帯の外で止まり、設定値が効かない時間がある。線形の model は 1 つの利得に平均する。
  2. 最初の 7.75 h の 30 ℃の区間。
- 段 2 に進むには、A の model（時間帯で分ける、在室の時間帯だけで学習する、など）か目的を見直す。新しい事前登録が要る。

## 手順 6：移転の検査（`transfer_policy.py`）

`scripts/px4_lab/transfer_check.py`、`artifacts/px4-transfer-check-20261108/record.json`（`8aa290ad…`）。

- 入力は次のとおり。
  - 学習した model。
  - 承認済みの ControlSpec と SafetyProfile（A：`excitation/cfg/safety.yaml`、B：`control/cfg/safety.yaml`）。
  - 対応付けの AI の下書き（`artifacts/px4-transfer-precheck-20261107/mapping-xfer-*.yaml`）。人の宣言ではない（ADR-0017 D2）。
  - 点の単位の証拠は、各 dataset の manifest のもの（`inferred`）。
- **`training-range` は A と B の両方で拒否された**（終了コード 1）。
  - 理由：ControlSpec の `action.point` は overlay の URI だが、dataset の `manifest.units` の key は RI の pointId（`BPT-0033`、`zone-101.temp-setpoint`）。
  - 範囲は、BDE の `training_action_range` と同じ式（`action_commanded__*` の min／max）で取った。A は 21.0〜30.0 ℃（既定の 30 ℃の区間を含む）、B は 21.0〜27.0 ℃。
- **`check` は両方の向きで拒否された**（各 3 件、`action_not_allowed`）。
  - 移転先の action の点（URI）が、承認済みの SafetyProfile の `control_eligible`、`hard_limits`、`units` に無い。承認済みの profile は RI の pointId で書かれている。
  - 2026-11-07 の事前確認は、生成器の雛形（URI で書かれている）を読んだので、この拒否が出なかった。
  - 範囲、変数、役割の拒否は無かった。
- `build` は、`check` が通らないので実行していない。
- 起票：BDE #928 (`private/building-decision-engine/issues/928`, not exported)（移転の CLI が、URI と RI の pointId を対応させずに照合する）。

## 段 1b：在室の時間帯だけで学習し直す（探索的、[事前登録](../preregistration/px4-stage1b.md)、sha256 `d90742f2…`、commit `1cd1f56`）

段 1 の結果の後、ユーザーが「段 1b」を選んだ（2026-11-08）。事前登録は、結果を見る前に commit した。

- データと窓は段 1 と同じ。sim の現地時刻（plant の `start_datetime` のオフセット。A は +09:00、B は −07:00）が 8:00〜18:00 の行だけを使う。
- 絞り込みは Testbed の driver（`--local-hours 8:18`）で行い、学習は BDE の `train_dynamics`。
- A の最初の 30 ℃の区間（現地 0:25〜8:10）は、この絞り込みで外れる。

| | A（`artifacts/px4-a-train-1b-20261108`） | B（`artifacts/px4-b-train-1b-20261108`） |
|---|---|---|
| 行（絞る前 → 後） | 576 → 240（学習 173、holdout 67） | 2016 → 840（学習 600、holdout 240） |
| holdout の 1 歩先の RMSE | 室温 0.582 K、冷房 0.234 kW、ファン 0.065 kW | 室温 0.656 K、冷房 0.143 kW、ファン 0.015 kW |
| model の定常の利得（室温／設定値） | **0.69 K/K**（外気 30.8 ℃） | **0.93 K/K**（外気 31.5 ℃） |
| 定常の室温（21／24／27 ℃） | 22.30／24.37／26.43 | 21.29／24.10／26.90 |
| results.json | 11 Pass／1 Fail（`5a9af480…`、Fail は段 1 と同じ `source_run_passed`） | 11 Pass／1 Fail（`cfd85568…`） |

replay（補遺と同じ手順。`artifacts/px4-{a,b}-weight-replay-1b-20261108/replay.json`、A `8a7961e9…`、B `6e300ea0…`）：

| 重み | A：内側（16 周期目） | A：16 周期目の中央値 | A：帯の外（K·h／4 h） | B：内側（16 周期目） | B：16 周期目の中央値 | B：帯の外 |
|---|---|---|---|---|---|---|
| 0.03 | 1.000 | 25.96 | 4.45 | 0.175 | 27.0 | 8.17 |
| 0.1 | 1.000 | 25.96 | 4.45 | **1.000** | 23.90 | 0.40 |
| 0.3 | 1.000 | 23.46 | 0.003 | 1.000 | 23.90 | 0.40 |
| 1.0 | 1.000 | 23.46 | 0.003 | 1.000 | 23.90 | 0.40 |

開始の state は A が 23、B が 80。

**段 1b の §4 の判定：重みは 0.1。** 両方のプラントで内側の割合が 0.5 以上になる、最も小さい候補である。

**段 2 の前に判断が要ること（結果を見た後の観察。判定は変えない）：**
- A は 0.1 のとき、提案が 26 ℃前後で、予測の室温は帯（22〜24 ℃）の上に 4.45 K·h 出る。端には張り付かないが、快適性の罰はほぼ効いていない。
- 0.3 では、A も B も提案が 23.5〜23.9 ℃で、帯の外は A 0.003、B 0.40 K·h。
- 基準の「内側の割合」は、範囲の端に張り付かないことしか見ていない。段 2 で 0.1 を使うか、帯の外も基準に入れて選び直すかは、段 2 の事前登録で決める。

**人の判断（2026-11-08、結果を見た後）：段 2 の重みは 0.3。** 帯の外も基準に入れて選び直す。
- 選び直しの規則：内側の割合が両方のプラントで 0.5 以上、かつ各プラントの帯の外が候補の中の最小から 0.1 K·h 以内になる、最も小さい重み。A は 0.3 と 1.0、B は 0.1 以上が当てはまり、0.3 になる。
- この規則は段 1b の結果を見てから作った。段 1b の §4 の判定（0.1）は書き換えない。段 2 の事前登録に、0.3 とこの経緯を書く。

## 変更

| ファイル | 内容 |
|---|---|
| `scripts/run_bde_pipeline.py` | PX4 の dataset の窓を、事前登録の励起の期間で切る（`score_window`）。段 1b の `--local-hours LO:HI`（plant の現地時刻で行を絞る）。E2E-04 と BOPTEST の既定は変えていない |
| `scripts/bde_pipeline/driver.py` | request に `local_hours` があれば、BDE が作った dataset の行を絞ってから学習する |
| `scripts/px4_lab/weight_replay.py` | 補遺の replay |
| `scripts/px4_lab/transfer_check.py` | 移転の検査（BDE の CLI を呼び、拒否をすべて記録する） |
| `tests/test_run_bde_pipeline.py`、`tests/test_px4_weight_replay.py` | 窓の切り方、重みの置き換え、内側と帯の外の数え方、選び方 |

## 残っていること

1. **人と AI：** 段 2 の事前登録。
   - 重みは 0.3（人の判断、上）。0.3 とその経緯を書く。
   - 在室の時間帯の model の使い方（評価の窓を在室の時間帯の中に置く）。
   - 閉ループのハーネスで方式を比べる設計。
2. **BDE：** #928 が直るまで、移転の検査は実際の承認済みの入力では通らない。段 2 の移した MPC はこれを待つ。
3. **人：** 移転の対応付けを宣言する。今は AI の下書きである。

## Rollback

この PR を revert する。artifacts（`px4-{a,b}-train-20261108{,b}`、`px4-{a,b}-train-1b-20261108`、`px4-{a,b}-weight-replay-1b-20261108`、`px4-{a,b}-weight-replay-20261108`、`px4-weight-generated-20261108`、`px4-transfer-check-20261108`）は消してよい。
