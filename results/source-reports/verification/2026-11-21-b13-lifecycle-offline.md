# B13（#71）制御のライフサイクル：シナリオ 1、2、3、5 の offline の再整理

**offline の再整理だけ。live、image、承認は使っていない。artifacts には何も書いていない（読んだだけ）。**

- 対象：#71 のシナリオ 1、2、3、5。シナリオ 4 は別の記録（[2026-11-21-b13-s4.md](2026-11-21-b13-s4.md)）で、ここでは引用だけする。
- 材料：既存の run の記録（PX3、PX4 stage 1、B3、PX5 F1）。新しい run は無い。
- Testbed：`958eee1`（branch `feat/b11-contract-layers`）。
- 性格：既知の結果を遷移ごとに並べ直したもの。新しい確証ではない。この文書で新しく読んだ値（lake の行、ledger）は「探索的」と書く。

## 1. 概念モデル

**これは概念モデルである。** 製品（BDE、RI、Nexus、hvac-sim）に、この形の状態機械が実装されているとは言わない。
各遷移は、記録のどこで観測できるかを整理するための区切りである。

| # | 遷移 | 主体 | 主な観測点（記録） |
|---|---|---|---|
| L0 | 要求（提案） | Testbed の proposer／BDE | `control/proposer/proposals.jsonl` |
| L1 | Safety の判定（approved／projected／rejected） | BDE Safety Runtime | proposals の `safety_decision`、Safety の ledger（`control/active-ledger.json`） |
| L2 | RI の受付（202 と controlId）、または拒否（4xx／503） | RI | Safety の `dispatch.status`（`ACCEPTED` は 202。[B3](2026-11-08-b3-injection.md) の「dispatch が ACCEPTED、つまり 202」）、B3 の trace の `status` |
| L3 | 配送 a：RI → connector | RI、Nexus | connector の log に同じ control_id が出る |
| L4 | 配送 b：connector → 機器（WriteProperty の ACK） | Nexus | RI の監査の行の `result`（`success`／`failed`）、connector の `wrote …` と `write timed out` |
| L5 | 適用：機器の priority 8 の slot に値が入る | 機器（plant） | plant の read-only の probe の priority の配列（`priority-*.json`） |
| L6 | 有効値：present value（priority の解決の結果）。Nexus が読み、RI に入る | 機器、Nexus、RI | RI の latest／history、lake の行（`zone-101.temp-setpoint` 等） |
| L7 | 実効値：plant が実際に使う setpoint | plant | feedback の点 `zone-101.temp-setpoint-active`（BACnet の priority の外の値） |
| L8 | 解除：release の受付と配送（priority 8 を null に） | Safety、RI、Nexus | release の dispatch、監査の行、connector の `released …` |
| L9 | 解除後の有効値：present value が次の priority か relinquishDefault になる | 機器 | 解除後の priority の配列と present value |
| L10 | 再同期：断の後に、要求側の状態（Safety の ledger）と機器の状態を合わせる | BDE Safety、RI | 断の後の proposals の判定、ledger、lake |

L6 と L7 を分けるのは、PX5 の plant（hvac-sim `64644ad`、supervisory あり）で present value と plant の実効の setpoint が食い違ったからである（§5、[s4](2026-11-21-b13-s4.md) の補足）。

### 検査と遷移の対応（どの検査が、どの遷移を見るか）

| 検査 | 見る遷移 | 出典 |
|---|---|---|
| S（`checks.s_flags`）／B11 の V0 | L2（2xx でない status、202 に controlId が無い）、L8 の status | `scripts/b3_lab/checks.py`、`scripts/b11_lab/layers.py` |
| C `fail-out-of-range-refused`、`t-schema-missing`、`pre-write-permission`、`t-invalid-release-value`（V1） | L2 の前提（範囲、schema、権限、解除の値） | 同上 |
| C `post-actor-result-recorded`（V2） | L4 の一部。監査の**行の数**が受付の数以上か。行の `result` の値は見ない | `checks.py` 172〜174 行 |
| C `post-readback`（V2） | L6。受け付けた値が読戻しに 1 度でも出るか | `checks.py` 169〜171 行 |
| C `post-default-readback`（V2） | L9。解除後に priority の配列が空で、present value が relinquishDefault か | `checks.py` 175〜178 行 |
| B12 `fail-release-failure-reported`（V3） | L8／L9。解除の非 2xx、または 2xx なのに値が残る | `scripts/b12_lab/v3.py` |
| verify `control_audit_success_by_safety_writer`、`control_connector_wrote_priority_8` | L4（全行が `success`、connector の書込の数が control_id の数と同じ） | `scripts/ri_lab/control_path.py` 615〜620 行 |
| verify `release_slot_8_held_the_last_active_value` | L5（解除の直前の slot 8 が、最後に `ACCEPTED` だった値と同じか） | `scripts/ri_lab/control_release.py` 219 行、`control_path.py` 627〜628 行 |
| verify `release_priority_array_all_null`、`release_present_value_is_relinquish_default` | L9 | `control_release.py` |
| `transactions.py`（PX3 以降の採点） | L1→L2→L4→L6 を control_id で追う（監査、connector、lake の 120 s 以内の行） | `scripts/px3_lab/transactions.py`、PX3 の準備 (`2026-11-06-px3-preparation.md`, not exported) |

- L7（実効値）と L10（再同期）を判定する検査は、S、C、V0〜V3、verify のどれにも無い。
- L3 と L4 を分けて判定する検査も無い。connector の log で読めるだけである。
- L5 は、plant の probe（Testbed の南側の read-only の読取）でしか見ていない。RI の API からは見えない。[B11](2026-11-21-b11-contract-layers.md) も「T12 の `post-default-readback` は、機器の priority の配列（南側）を読まないと出ない」と書いている。

## 2. 版の違い

run ごとに SHA が違う。論文では違いを明記するか、1 つの組合せで走らせ直す（#71 の注意）。

| run | hvac-sim | RI | BDE | Nexus | 出典 |
|---|---|---|---|---|---|
| PX3 A run 3、B run 1 | B は `2eb52e4`（A は BOPTEST `0f8a467`） | `e87cc65` | `149056d` | `76839b0` | manifest `px3-b-px1-path`、`px3-a-run3` |
| PX4 stage 1 A run 2、B run 1 | B は `2eb52e4`（A は BOPTEST `0f8a467`） | `8c87146` | `5f36355` | `76839b0` | manifest `px4-a-boptest-path`、`px4-b-px1-path` |
| B3（T10、T12） | `2eb52e4` | `8c87146` | `5f36355` | `76839b0` | manifest `b3-lab-px4-b-path.overrides` |
| PX5 F1 | `64644ad`（supervisory あり） | `8c87146` | `5f36355` | `76839b0` | manifest `px5-b-faults.overrides` |
| シナリオ 4 run 1 | `64644ad` | `8c87146` | `5f36355` | — | [s4](2026-11-21-b13-s4.md) |

- image も違う。PX4 B の plant の image は 2026-11-08 に作り直した（`8db89e36…`、manifest `px4-b-px1-path.plant_image_deviation`）。B3 の RI の実行用の image は `ec20219d…`（今は無い）、PX5 は `f3b93cdf…`（manifest `b3-lab-px4-b-path.ri_runtime_image` の注、`px5-b-faults.ri_runtime_image`）。B3 の plant の image の ID は、manifest の B3 の entry に記録が無い（**不明**）。
- PX3 だけ RI と BDE が古い（`e87cc65`、`149056d`）。PX4、B3、PX5 は RI `8c87146`、BDE `5f36355` で同じ。
- hvac-sim は 2 つある。`2eb52e4` は supervisory が無く、`64644ad` は supervisory（timeout_s 300、fallback の schedule）がある（manifest `px5-faults.experiment.decisions` P5-D1）。

## 3. シナリオ 1：正常な書込・適用・読戻し

材料：PX3 A run 3、PX3 B run 1、PX4 A run 2、PX4 B run 1。

| run | verify（results の sha256） | 採点 | 出典 |
|---|---|---|---|
| PX3 B run 1 | 164 Pass／0 Fail（`01808316…`） | 一致 96／96、release 1／1、不正な書込 0。判定 approved 94、projected 2（`artifacts/px3-b-run1-20261106/px3-transactions/transactions.json`、`93bc9f76…`） | manifest `px3-b-px1-path.path_run` |
| PX3 A run 3 | 169 Pass／0 Fail（`24401338…`） | 一致 96／96、release 1／1、不正な書込 0（`artifacts/px3-a-run3-score-20261107/transactions.json`、`d99d4ac7…`） | manifest `px3-a-run3.experiment.results` |
| PX4 A run 2 | 168 Pass／1 Fail（`e336b6a1…`。Fail は RI #657） | 一致 192／192、release 1／1、不正な書込 0。判定 approved 152、projected 9、rejected 31（`2d068f02…`） | manifest `px4-a-boptest-path.path_run` |
| PX4 B run 1 | 163 Pass／1 Fail（`db0090f3…`。Fail は RI #657） | 一致 672／672、release 1／1、不正な書込 0。判定 approved 624、projected 48、rejected 0（`4d64d65d…`） | manifest `px4-b-px1-path.path_run` |

- 4 つの run の results.json を読み、下の表に挙げた verify の検査（10 個）がすべて Pass であることを確かめた。
- 「一致」は、拒否の提案では「何も dispatch されない」ことを一致とする（PX3 の準備 (`2026-11-06-px3-preparation.md`, not exported)、P3-4）。

| 遷移 | 観測 | 証拠 | 検査 | 結果 |
|---|---|---|---|---|
| L0 要求 | yes | proposals.jsonl（各 run） | `transactions.py` | Pass（96、96、192、672 件） |
| L1 Safety の判定 | yes | proposals、ledger | `transactions.py`、verify `control_every_cycle_decided_by_safety` | Pass |
| L2 RI の受付 | yes | dispatch `ACCEPTED` と control_id | `transactions.py`（監査の行と同じ id） | Pass |
| L3 配送 a | yes | connector.log に control_id | `transactions.py` | Pass |
| L4 配送 b | yes | 監査の行が `success`、connector の `wrote … priority=8` | verify `control_audit_success_by_safety_writer`、`control_connector_wrote_priority_8`、`control_audit_row_per_accepted_write` | Pass（4 run とも） |
| L5 適用（slot 8） | partly | 解除の直前の 1 回だけ。PX3 B は slot 8 = 22.5、present value 22.5（`artifacts/px3-b-run1-20261106/control/priority-before-release.json`）。書込ごとの slot は読んでいない | verify `release_slot_8_held_the_last_active_value` | Pass（4 run とも。最後の書込だけ） |
| L6 有効値（present value） | yes | lake の行（書込の後 120 s 以内に同じ値） | `transactions.py`（PX3 A は採点 v2、float32 の許容） | Pass |
| L7 実効値 | partly（記録はあるが判定は無い） | lake の `zone-101.temp-setpoint-active`（探索的、下記） | なし | **Not Tested** |
| L8 解除 | yes | release の dispatch、監査、connector の null の書込 | verify `release_safety_approved_and_dispatched_value_1`、`release_audit_row_success_by_safety_writer`、`release_connector_wrote_null_at_priority_8` | Pass（4 run とも） |
| L9 解除後の有効値 | yes | PX3 B は配列がすべて空、present value 28.0 = relinquishDefault 28.0（`priority-after-release.json`） | verify `release_priority_array_all_null`、`release_present_value_is_relinquish_default` | Pass（4 run とも） |
| L10 再同期 | — | 断が無い | — | 対象外 |

**探索的（この文書で読んだ。判定に使わない）：L6 と L7 の食い違い。**

- 読み方：`telemetry/retrieved-*.parquet` を id で重複を除いて読み、同じ時刻の `zone-101.temp-setpoint` と `zone-101.temp-setpoint-active` の値を比べた。
- PX3 B run 1：1556 組のうち 73 組で違う。連続は 11 回で、最長 50 s（11 行、19:44:04〜19:44:54Z、setpoint 28.0 に対し active 22.5。release の直後）。
- PX4 B run 1：2513 組のうち 18 組で違う。どれも 1 行だけ。
- 書込や release の後の短い遅れに見えるが、原因は確かめていない。PX3 A（BOPTEST）では読んでいない。

## 4. シナリオ 2：受付の後、配送が失敗

2 つの記録は形が違う。

- **PX5 F1 の 22.5 の書込**は、RI が受け付けた（dispatch `ACCEPTED`）後に、connector から機器への書込が timeout した。#71 の「受付の後、配送が失敗」そのものである。
- **B3 T12 の解除**は、RI が 503 を返した。**受付の前の失敗**であり、厳密には「受付の後」ではない。結果として、機器の priority 8 に値が残った。

### 4.1 PX5 F1（+600 s の書込）

材料：`artifacts/px5-f1-run-20261110b`（results `8615db9e…`）、score `fed6955d…`、transactions `30747e22…`、events `aa3cd002…`（manifest `px5-b-faults.live.runs.f1`）。
入力の sha256 は、score.json と transactions.json の `inputs_sha256` にある（proposals `b1c0139a…`、connector.log `7bd51f43…`、監査 `44d6b996…`）。

| 時刻（UTC） | 記録 | 出典 |
|---|---|---|
| 19:49:16.164 | connector を plant の network から切った | events.json `disconnect` |
| 19:49:16.849 | 提案 22.5。Safety は approved（checks はすべて true、staleness 1.3 s）。dispatch `ACCEPTED`、control_id `54a4e89b…` | proposals.jsonl 11 行目 |
| 19:49:16.898 | ledger `le-9ed42ed1cf54`：dispatch `ACCEPTED`、`completed_at` null | active-ledger.json |
| 19:49:21.902 | RI の監査：`failed`、`timeout`（created 19:49:16.881 から 5.0 s） | control-audit.log 11 行目 |
| 19:49:26.905 | connector：`write timed out for analogValue,1 control_id=54a4e89b…` | control/connector.log 13 行目 |

| 遷移 | 観測 | 証拠 | 検査 | 結果 |
|---|---|---|---|---|
| L0、L1 | yes | proposals、ledger | `transactions.py` | approved |
| L2 RI の受付 | yes | dispatch `ACCEPTED`、control_id | S／V0 は見ない（PX5 は B3 の trace を作っていない） | 受付あり |
| L3 配送 a | yes | connector の log に同じ control_id（timeout の行） | 判定する検査なし | 届いた |
| L4 配送 b | yes | 監査 `failed`／`timeout`、connector の書込の行は 10 件で 22.5 は無い（`connector-writes.log`） | verify `control_audit_success_by_safety_writer`、`control_connector_wrote_priority_8`、`transactions.py`（「audit row differs」「no connector write」） | **Fail**（失敗を検出した） |
| L5 適用 | yes（解除の直前に 1 回） | slot 8 = 24.0（22.5 ではない）、present value 24.0（20:19:47Z、`priority-before-release.json`） | verify `release_slot_8_held_the_last_active_value` | **Fail**（下記） |
| L6 有効値 | yes | lake の setpoint は 19:40:19 から 20:19:59 まで 24.0。22.5 の行は無い。19:49:15〜20:04:22 は行が無い（断） | `transactions.py` | 22.5 は一致しない（39／40） |
| L7 実効値 | yes（探索的） | §6 | なし | Not Tested |
| Safety への結果の戻り | yes | ledger の 40 行すべてで `completed_at` は null、`actual_bms_value` は null。`ACCEPTED` の 11 行に 22.5 の行も入る | なし | 監査の `failed` は ledger に反映されていない |

- `release_slot_8_held_the_last_active_value` は、「最後に dispatch が `ACCEPTED` だった提案の final_value」を基準にする（`control_path.py` 627〜628 行）。F1 の基準は 22.5 で、slot 8 は 24.0 だったので Fail した。この検査も「受付 = 適用」と置いている。slot 8 は、最後に**配送できた**値（24.0）を正しく持っていた。
- `unauthorized_writes` の 1 件（`54a4e89b…`）は、この監査の行である（PX5 (`2026-11-11-px5-live.md`, not exported) の F1 の 6）。
- B3 の S／C、B11／B12 の層は、PX5 の記録には当てていない（trace の形が無い）。当てたときの判定は **Not Tested**。

### 4.2 B3 T12（解除の 503）

材料：`artifacts/b3-lab-run-approved-20261109b/control/b3/results.json`（sha256 `86eec024…`、manifest の `b3_results_sha256` と同じ）、control-audit.log、[B3](2026-11-08-b3-injection.md)。

| 遷移 | 観測 | 証拠 | 検査 | 結果 |
|---|---|---|---|---|
| 書込 15.0：L1〜L4 | yes | Safety approved、202、controlId `c24062ab…`、監査 `success` | — | 正常 |
| 書込 15.0：L5、L6 | yes | 解除の前の slot 8 = 15.0、present value 15.0（20:35:37Z） | — | 正常 |
| 解除：L1 | yes | Safety approved（final 1.0）、dispatch `GATEWAY_OFFLINE` | — | — |
| 解除：L2 | yes | RI は **503**。監査の行は `failed`、`target gateway is not currently connected` | S（`release: status 503`）、B12 V3 `fail-release-failure-reported`（探索的に当てた。下記） | **検出** |
| 解除：L3、L4 | no | RI が受け付けていない | — | 起きていない |
| L9 解除後の有効値 | yes | 解除の後（20:37:17Z）も slot 8 = 15.0、present value 15.0、relinquishDefault 12.0 | C `post-default-readback`（V2） | **検出** |

- B11 の判定では、T12 は V0 で最初に検出（503）、V2 で `post-default-readback` が加わる（[B11](2026-11-21-b11-contract-layers.md)）。
- 探索的：`scripts/b12_lab/v3.py` の `judge` を T12 の trace に当てた（stdout だけ、artifacts に書いていない）。V3 で `fail-release-failure-reported` が加わる。最初の層は V0 のまま。

## 5. シナリオ 3：受付値と適用値が違う（B3 T10）

材料：`artifacts/b3-lab-run-clamp-20261109/control/b3/results.json`（sha256 `a939eaf7…`、manifest と同じ）、`control/relay/relay.jsonl`、control-audit.log、[B3](2026-11-08-b3-injection.md) 逸脱 11。

| 遷移 | 観測 | 証拠 | 検査 | 結果 |
|---|---|---|---|---|
| L1 Safety | yes | approved、final 16.5（hard limit [13, 17] の中） | — | — |
| L2 RI の受付 | yes | 202、controlId `53c8679f…` | S／V0 | 見落とす（正しい 202） |
| L3、L4 配送 | yes | 中継が `analogValue,2` の WriteProperty を 16.5 → 16.0 に書き換えた（`clamped`、priority 8、書き換え 1 件）。plant の SimpleACK はそのまま返る。監査は `success`、`ok` | C `post-actor-result-recorded`（行の数だけ見る） | 見落とす（監査は成功） |
| L5 適用 | yes | 機器の slot 8 = 16.0、present value 16.0、relinquishDefault 12.0（trace の `device`） | 判定する検査なし（trace に残すだけ、逸脱 11） | 16.0 |
| L6 有効値 | yes | latest の読戻し 16（期待 16.5） | C `post-readback`（V2） | **検出** |
| L7 実効値 | no | AHU の給気温度の setpoint の feedback の点は RI の snapshot に無い（`ahu-1.sat-setpoint` と `.release` だけ） | なし | Not Tested |
| L8、L9 解除 | no | T10 の trace の `release_after` は null。results の `priority` も before／after とも null | — | Not Tested |

- B11：T10 は V2 で最初に検出（`post-readback`）。探索的に B12 の `v3.judge` を当てても、V3 で加わる条件は無い。
- 監査の `success` は、機器の ACK を意味するだけで、受け付けた値が適用されたことは意味しない。T10 はその反例である。
- 注入点は機器ではなく Testbed の中継である。hvac-sim `2eb52e4` は範囲外を拒否し、丸めない（B3 逸脱 11）。

## 6. シナリオ 5：通信断から復帰し、再同期する（PX5 F1）

材料は §4.1 と同じ。加えて、plant の audit（`artifacts/px5-f1-plant-20261110b/audit/audit.jsonl`、6 行）、lake の行（探索的）を読んだ。
ledger（`control/active-ledger.json`）と plant の audit の sha256 は manifest に記録が無い。この文書で計算した値は、ledger `489ef265…`、plant の audit `20d24d96…`。

### 6.1 状態遷移の列（記録から）

Safety の override-detect の規則は `zone-101.temp-setpoint=0.5:600`（deadband 0.5、停止 600 s。manifest `px5-b-faults.prepared.safety_inputs_149056d.typed_rules`）。staleness の上限は 180 s（`px5-b-faults.pin_note`）。

| 時刻（UTC） | offset | 要求側（Safety の判定、ledger） | 機器側（BACnet と plant） | 出典 |
|---|---|---|---|---|
| 19:39:16〜19:48:16 | 0〜540 | 11 提案、approved 10、projected 1。`ACCEPTED` 10 件、監査 `success` 10 件 | connector の書込 10 件。setpoint 26.0 → 24.0 | proposals、control-audit.log、connector-writes.log、lake |
| 19:45:24〜19:46:20 | — | — | active が 28.0 になり、19:46:25 に 24.0 に戻る（setpoint は 24.0 のまま）。plant の audit は 19:46:16 に `old 28.0 → new 24.0` | lake（探索的）、plant の audit |
| 19:49:16 | 600 | 断。22.5 を approved、`ACCEPTED`。ledger は `completed_at` null のまま | 22.5 は届かない。監査 `failed`／`timeout` | §4.1 |
| 19:49:15〜20:04:22 | — | — | lake に setpoint と active の行が無い | lake（探索的） |
| 19:50:16 | 660 | rejected：「手動 override を検知: BDE が書いた 22.5 に対し applied 24.0（deadband 0.5）」。staleness 61.3 s（上限の内、`staleness` の check は true）。state の値は 19:49:16 と同じ（室温 23.952） | — | proposals 12 行目、ledger `le-94ebaa6caf5f` |
| 19:51:15〜20:00:15 | 720〜1260 | rejected：「手動 override のため残り N s は書込を停止」（541 → 1 s）。19:52:15 から `stale state`、19:55:15 から `stuck state` が加わる | — | proposals |
| 20:01:15 | 1320 | rejected：override を**再び検知**（22.5 対 24.0） | — | proposals |
| 20:04:15.899 | 1500 | つなぎ直し | — | events.json `connect` |
| 20:04:22 | — | — | lake の行が戻る。setpoint 24.0、**active 28.0** | lake（探索的） |
| 20:05:15〜20:10:15 | 1560〜1860 | rejected：停止の残り（360 → 60 s）だけ。staleness 3.5 s 以下で、`stale`、`stuck` は消えた | setpoint 24.0、active 28.0 | proposals、lake |
| 20:11:15 | 1920 | rejected：override を**3 回目に検知**（22.5 対 24.0） | 同上 | proposals |
| 20:12:15〜20:18:15 | 1980〜2340 | rejected：停止の残り（540 → 180 s）。最後の提案 | 同上 | proposals |
| 20:19:47 | — | — | 解除の直前：slot 8 = 24.0、present value 24.0、relinquishDefault 28.0 | `priority-before-release.json` |
| 20:19:55 | — | release：監査 `success`、connector `released analogValue,1 priority=8` | — | control-audit.log 12 行目、connector.log 193 行目 |
| 20:21:26 | — | — | 配列はすべて空、present value 28.0 | `priority-after-release.json` |

- ledger は 40 行。`ACCEPTED` 11 行（22.5 を含む）、`SKIPPED_REJECTED` 29 行。どの行も `completed_at` と `actual_bms_value` が null だった。
- lake（探索的）：setpoint と active が同じ時刻で違う組は 707 組のうち 201 組。最長の連続は 20:04:22〜20:19:54Z の 187 行（約 933 s）で、setpoint 24.0 に対し active 28.0。
- plant の audit は 6 行で、最後は 19:46:16。22.5 の行も、解除の行も無い。plant の audit が何を記録するかは確かめていない。

### 6.2 遷移ごとの判定

| 遷移 | 観測 | 証拠 | 検査 | 結果 |
|---|---|---|---|---|
| 断の検知（stale） | yes | `stale state` は 19:52:15（断から約 179 s）から。最初の停止の理由は override（60.7 s） | PX5 の主要な指標 `f1_detection_s`（理由に `stale state`、≤ 300 s） | **Fail**（理由が違う、PX5 (`2026-11-11-px5-live.md`, not exported)） |
| 断の間の書込 | yes | connector の書込 0 | `f1_writes_during_fault`（= 0） | Pass |
| L10 再同期：機器の状態の取り直し | yes | つなぎ直しの後、staleness は 3.5 s 以下に戻り、`stale`、`stuck` の理由は消えた | なし | 状態の読取は戻った（判定なし） |
| L10 再同期：要求側の基準の更新 | yes | override の基準は 20:11:15 にも 22.5（配送できなかった値）のまま。機器の値 24.0 との差 1.5 は deadband 0.5 より大きい | なし | 更新されなかった |
| 書込の再開 | yes | つなぎ直しから run の終わり（+2340 s）まで書込 0 | `f1_recovery_s`（≤ 180 s） | **Fail** |
| L6 と L7 の一致（再接続の後） | yes（探索的） | present value 24.0、実効 28.0 が約 933 s 続く | なし | Not Tested（食い違いを記録） |
| L8、L9 解除 | yes | 監査 `success`、配列は空、present value 28.0 | verify `release_priority_array_all_null`、`release_present_value_is_relinquish_default` | Pass |

### 6.3 原因の見込み（仮説。BDE の code では確かめていない）

**仮説：** BDE Safety の override の検知は、最後に dispatch が `ACCEPTED` になった値を「BDE が書いた値」として使う。配送の失敗（RI の監査の `failed`）は Safety に戻らない。そのため、配送できなかった 22.5 が基準に残り、機器の値（24.0）との差が消えない。

根拠（すべて記録から）：

1. override の理由の文が、3 回とも「BDE が書いた 22.5 に対し applied 24.0」である（19:50:16、20:01:15、20:11:15）。22.5 は監査で `failed` の書込の値で、機器にも lake にも現れない。
2. ledger の 22.5 の行は `ACCEPTED` のままで、`completed_at` は null。40 行すべてで `completed_at` と `actual_bms_value` が null である。
3. 「applied 24.0」は、最後に配送できた書込（19:48:16、監査 `success`）の値、解除の直前の slot 8、lake の present value と同じである。実効の setpoint（28.0）とは違う。
4. 再検知の間隔は、停止の 600 s と合う（19:50:16 → 20:01:15 → 20:11:15）。停止の間は書込が無いので、基準の 22.5 は上書きされない。停止 → 再検知がくり返される形になる。

言えないこと：

- Safety が「applied」をどこから読むか（RI の latest か、別の経路か）は、記録からは分からない。値は present value と一致する。
- この振る舞いは BDE の製品の振る舞いである。Testbed では直さない。BDE への起票は未起票（#71、PX5 (`2026-11-11-px5-live.md`, not exported)）。
- 断の後、plant の実効の setpoint が 28.0 だったのは、hvac-sim `64644ad` の supervisory（timeout_s 300）の fallback と読める。ただし、plant の audit にその行は無く、確かめていない。

## 7. まとめの表（遷移 × シナリオ）

記号：Pass／Fail は、その遷移の期待（正常系では「起きる」、故障系では「検査が失敗を検出する」）に対する結果。NT は Not Tested。— は対象外。

| 遷移 | 1 正常（PX3、PX4） | 2 配送の失敗（F1 の 22.5 ／ T12） | 3 受付値 ≠ 適用値（T10） | 4 解除の後の priority 16（[s4](2026-11-21-b13-s4.md)） | 5 断と再同期（F1） |
|---|---|---|---|---|---|
| L1 Safety の判定 | Pass | approved ／ approved | approved | 記録あり（approved 38、projected 2、s4 E6） | approved の後 rejected 29 |
| L2 RI の受付 | Pass | 202 ／ **503**（S と V3 が検出） | 202（S は見落とす） | 判定なし | 断の後は dispatch されない |
| L3 配送 a | Pass | 届いた ／ 起きていない | 届いた | 判定なし | — |
| L4 配送 b | Pass | **失敗**（verify と transactions が検出）／ 起きていない | 書き換えて ACK（監査 `success`、検出なし） | 判定なし | 断の間 0 |
| L5 適用（slot 8） | Pass（最後の 1 回だけ） | 24.0 が残る（verify の slot の検査は Fail、基準が 22.5）／ 15.0 が残る | 16.0（判定なし） | E1 Pass（slot 8 = 23.5、slot 16 = 26.0） | 24.0 |
| L6 有効値（present value） | Pass | 22.5 は出ない（transactions 39／40）／ 15.0 | **16**（C `post-readback` が検出） | E1 Pass | 24.0 |
| L7 実効値 | NT（探索的には短い遅れだけ） | NT | NT（点が無い） | NT（補足：26.0 に対し実効 28.0） | NT（探索的には 24.0 に対し 28.0 が約 933 s） |
| L8 解除 | Pass | Pass（F1）／ **503** | NT | 判定なし（verify の release の検査は E3 として記録） | Pass |
| L9 解除後の有効値 | Pass | Pass（F1）／ 15.0 が残る（C `post-default-readback` が検出） | NT | E2 Pass（26.0）。E5 **NT**（retry 待ち） | Pass |
| L10 再同期 | — | — | — | — | **Fail**（要求側の基準が更新されず、書込が再開しない） |

- シナリオ 4 は run 1 で E1、E2 が Pass、E5 が Not Tested（runbook の欠陥）。retry は live queue に入っている（[s4](2026-11-21-b13-s4.md)）。
- 契約の検査（S、C、V0〜V3）が見るのは L2、L4 の行の数、L6、L9 だけである。L3 と L4 の区別、L5、L7、L10 は、どの層にも入っていない。

## 8. 限界

- 新しい run は無い。各シナリオは既存の run の 1 本ずつで、くり返していない。
- シナリオごとに SHA と image が違う（§2）。とくに PX3 は RI と BDE が古く、シナリオ 5 だけ hvac-sim が `64644ad`。
- T12 は「受付の前の失敗」で、#71 の「受付の後、配送が失敗」とは形が違う。受付の後に解除の配送が失敗する記録は無い（**Not Tested**）。
- T10 の注入点は Testbed の中継で、機器そのものではない。
- 「探索的」と書いた値（lake の setpoint と active の比べ、ledger の数え、B12 の `v3.judge` を T10／T12 に当てたもの）は、この文書を書くときに読んだもので、事前登録も artifacts も無い。判定に使わない。
- シナリオ 5 の原因は仮説である。BDE の code は読んでいない。

## 9. 次

- シナリオ 4 の retry の結果を s4 の記録に足す（別の作業）。
- シナリオ 5 の仮説を BDE に起票するかは、人が決める。直った後に F1 をやり直すときは、事前登録と承認をやり直す。
- 受付の後に解除の配送が失敗する場合（release の 202 の後に connector を切る）は、記録が無い。要るなら新しい事前登録で行う。
- verify の `release_slot_8_held_the_last_active_value` は「`ACCEPTED` = 適用」と置いている。配送の失敗がある run では基準を監査の `success` にするかを、Testbed の課題として検討する（この文書では変えない）。

## Rollback

この文書を消す。製品、artifacts、manifest には触れていない。
