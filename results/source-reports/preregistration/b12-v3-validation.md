# B12：事前に固定した検証用の注入の集合で V3 を測る（事前登録、#70）

この文書は、**V3 の述語を書く前に、また最初の注入の前に** commit する。commit の後に、注入の集合、選び方、V3 の定義、数え方を書き換えない。変えるときは新しい文書にし、結果を見た後であることを書く。

- 論文：bde-paper `f988200`。予備査読の指摘 1（契約の有効性、検証の選択バイアス）。
- 層 V0〜V2 は [`b11-contract-layers.md`](b11-contract-layers.md) のまま使う。述語は `scripts/b3_lab/checks.py`（変えない）。
- 契約試験一式 `bos-contract-suite-v0`（`ce211aa4…`）。

## 1. 開発用の集合と検証用の集合

- B3 の 13 件（T1〜T12）は**開発用の集合**である。V3 は B1 で gap だった条件を、B3 の結果を見た後に足すものだからである。開発用の集合で V3 の性能を主張しない。
- この文書の注入（下の §3）は**検証用の集合**である。V3 の述語は、この集合の結果を見る前に書いて commit する。
- 機械的な規則が開発用の注入と同じものを生んだら、検証用の集合から外す。外した物は §3 に書く。

## 2. V3 の条件

V3 = V2 ＋ 次の 4 つ。suite v0 で gap か conflict の条件のうち、Testbed の trace で判定できるものだけを選ぶ。`authorized_query` は B4 で扱うので外す。

| 条件 id | suite の状態 | 述語（flag を立てるとき） |
|---|---|---|
| `post-unit` | gap | 読んだ行の値が、その Point の単位の妥当な範囲の外にある。範囲は下の表で固定する |
| `fail-missing-not-filled` | conflict | 値の無い frame（null、NaN、±Inf）について、次のどちらか。(a) 拒否された（観測した拒否）。(b) 受け付けられ、同じ Point と時刻の行が有限の数値を持つか、その時刻の行が無い（埋めた、または黙って落とした） |
| `fail-unverifiable-refused` | conflict | twin の ControlSchema が欠けている（`dataType`、`minValue`、`maxValue` のどれかが無い）Point への書込について、次のどちらか。(a) 拒否された（観測した拒否）。(b) 2xx で受け付けられた（違反） |
| `fail-release-failure-reported` | gap | 解除の要求について、次のどちらか。(a) 2xx でない（観測した失敗）。(b) 2xx なのに、解除の後の priority の配列が空でないか、present value が relinquishDefault でない（黙った失敗） |

- flag の数え方は B2 §3.2 と同じ（観測した拒否、または契約違反）。したがって、正しく「欠測の行」を返したときは flag が立たず、「検出なし」と数える。この数え方の癖は、結果と一緒に書く。
- `post-unit` の妥当な範囲（単位 → [下限, 上限]）：K [173.15, 373.15]、degC [-100, 100]、W [0, 1e8]、W/m2 [0, 2000]、Pa [0, 2e5]、ppm [0, 1e5]、kg/s [0, 1e3]、m/s [0, 100]、%（または `percent`）[0, 100]。表に無い単位の Point は判定しない（Not Applicable と数える）。
- V3 の述語は、この commit の後に `scripts/b12_lab/v3.py` に書く。その commit の SHA を results に記録する。

## 3. 検証用の注入の集合

### 3.1 選び方（機械的な規則）

条件ごとに、条件の文が名指す違反の種類から、決まった演算子の族を作る。対象は B3 と同じ Point（telemetry は fixture の `BPT-0009`、K。control は lab の `ahu-1.sat-setpoint`）に固定する。

| 条件 | 演算子の族 | 適用 |
|---|---|---|
| `post-unit` | 同じ量（温度）の、他の単位で値を表す。UCUM の温度の単位から、degC、degF、mK、degR | 295.15 K を各単位に直した値を送る |
| `fail-missing-not-filled` | 値の無さの表し方：null、NaN、+Inf、「有効な frame の後の null」 | 各 1 frame（最後のものは 2 frame） |
| `fail-unverifiable-refused` | ControlSchema の 3 つの triple（`dataType`、`minValue`、`maxValue`）の空でない部分集合を外す。policy は既定の allow | 15.0 ℃ を書く |
| `fail-release-failure-reported` | 南側の経路の要素を 1 つ使えなくしてから解除する：gateway、connector の plant への network、plant | 15.0 ℃ を書き、使えなくしてから解除し、戻す |

### 3.2 開発用の集合と重なって外した物

| 生んだ注入 | 重なった開発用の注入 |
|---|---|
| K の Point に degC の値 | T1 |
| 単独の null の frame | T3 |
| 3 つの triple をすべて外す（allow） | T8 |
| gateway を止めて解除 | T12 |

### 3.3 集合（11 件）

| id | 条件 | 注入 | 層 |
|---|---|---|---|
| U1 | `post-unit` | `BPT-0009` に 71.6（degF） | telemetry（RI の部品、1 process） |
| U2 | `post-unit` | `BPT-0009` に 295150（mK） | 同上 |
| U3 | `post-unit` | `BPT-0009` に 531.27（degR） | 同上 |
| M1 | `fail-missing-not-filled` | 値が NaN の frame | 同上 |
| M2 | `fail-missing-not-filled` | 値が +Inf の frame | 同上 |
| M3 | `fail-missing-not-filled` | 295.15 の frame の 60 s 後に、値の無い frame | 同上 |
| S1 | `fail-unverifiable-refused` | twin から `dataType` だけを外す。allow で 15.0 を書く | control（L1 の lab の stack） |
| S2 | `fail-unverifiable-refused` | twin から `minValue` と `maxValue` を外す。allow で 15.0 を書く | 同上 |
| S3 | `fail-unverifiable-refused` | twin から `maxValue` だけを外す。allow で 15.0 を書く | 同上 |
| R1 | `fail-release-failure-reported` | 15.0 を書き、Nexus の connector を plant の network から外してから解除する。その後つなぎ直す | 同上 |
| R2 | `fail-release-failure-reported` | 15.0 を書き、plant の container を一時停止（`docker pause`）してから解除する。その後再開する | 同上 |

- 3 つの triple の部分集合は 7 つある。そのうち「3 つすべて」は T8 と重なるので外した。残り 6 つのうち、S1〜S3 の 3 つに絞った（各 triple を少なくとも 1 回外し、単独と組の両方を含む）。この絞り込みは作者の選択であり、限界に書く。
- control の注入は、1 件ごとに使い捨ての stack を 1 つ使う（5 run）。順番は S1、S2、S3、R1、R2。
- 書込の値 15.0 と解除の値 1 は、承認済みの lab の Safety（[13, 17] ℃、解除 {0, 1}）を値のまま通る。承認済みの hard limit と Safety の profile は替えない。注入の道具に、書込の credential を渡さない。

## 4. 測る物

- 各注入について、V0〜V3 の各層で検出したか、targeted か、最初に検出した層を数える（B11 と同じ数え方）。
- 正常な入力（B11 と同じ 163,394 件）に V3 を当てた誤検出を数える。
  - `post-unit`：telemetry の各行の値を、その行の Point の単位（run の `ri-snapshot.json`）の範囲で判定する。表に無い単位の行は Not Applicable として、判定した件数から外す。
  - `fail-missing-not-filled`、`fail-unverifiable-refused`：正常な入力には値の無い frame と schema の欠けた Point の書込が無いので、Not Applicable。
  - `fail-release-failure-reported`：解除の 2 件に当てる。
- 仮説は置かない。結果をそのまま報告する。検出できなかった注入も、そのまま報告する。

## 5. 実行の層と構成

- telemetry：B3 と同じ。RI `8c87146` の部品を 1 つの process で動かす（`scripts/b3_lab/telemetry/Program.cs` と同じ作り。B12 の注入だけを持つ別の Program を作る）。
- control：B3 の lab の構成（configuration `b3-lab-px4-b-path`、plant は PX4 B の hvac-sim `2eb52e4`、RI `8c87146`、BDE `5f36355`）。
  - 違い 1：Safety の承認は新しい物（`artifacts/b12-lab-safety-inputs-unapproved-20261121`、human:<approver>、2026-11-21T13:46:27Z）。材料は B3 の承認前の材料と byte で同じ。
  - 違い 2：RI の実行用の image は `building-os-e2e-ri-runtime@sha256:f3b93cdf…`（B3 の `ec20219d…` は消えた。PX5 の補遺 §8、PX4 段 2 の補遺 ri-runtime と同じ）。
  - 違い 3：plant の image は、同じ context から作り直した `2eb52e4`（ID `acf7f8eb…`）。
- live は直列。BOPTEST の時間の主体は使わない。後片付けは自分が所有する資源だけ。

## 6. 止める条件とやり直し

- 承認の鮮度（2026-11-22T13:46:27Z）までに終わらない run は始めない。
- Safety が RI の前で拒んだ注入は Not Tested（B2 §3.2）。
- 環境の失敗（書込の前に止まった）は、新しい stack で 1 回だけやり直せる。書込の後の失敗は、やり直さずに報告する。
- R1、R2 で、使えなくした要素を戻せなかったときは、その stack を片付けて次へ進む。plant と stack は使い捨てである。

## 7. 受入

- この文書の commit が、`scripts/b12_lab/v3.py` の最初の commit と、最初の注入より前にあること。試験で確かめる。
- `results.json`（SHA、`checks.py` と `v3.py` の sha256、各注入の層ごとの判定、正常な入力の誤検出）と `docs/verification/`。Pass／Fail／Skip／Not Tested を分けて書く。

## 8. 限界（先に書く）

- 注入の集合を作ったのは作者（AI）であり、独立した評価ではない。演算子の族の選び方と、S の 3 つへの絞り込みには、作者の選択が残る。
- telemetry の fixture の温度の Point は K だけである。degC の Point に degF を送る（妥当な範囲の中に入りうる）場合は試せない。
- `post-unit` は妥当な範囲による検査であり、同じ範囲に入る単位の取り違えは検出できない。
- 各注入は 1 回だけである。
