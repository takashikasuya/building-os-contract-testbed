# B12（#70）V3 の条件の検証（2026-11-21〜22）

- 事前登録：`docs/preregistration/b12-v3-validation.md`（commit 78d0508、sha256 cc2b4cf3…）。`scripts/b12_lab/v3.py` の最初の commit（71209b9）と、最初の注入より前
- 承認：human:<approver>（TTY）2026-11-21T13:46:27Z〜34Z（`manifest.yaml` `live_day_20261121.b12_control`）。AI は承認していない
- 集計：`scripts/b12_lab/summary.py` → `artifacts/b12-summary-20261122b/results.json`（sha256 c7e26861…、R1、R2 は試行 3）。1 回目は `artifacts/b12-summary-20261121/results.json`（sha256 19010340…）。各 trace を commit 済みの `v3.py` で判定し直す。live の呼び出しは無い
- 経路（control）：hvac-sim plant → Nexus → RI `8c87146`（runtime `f3b93cdf…`）→ BDE Safety `5f36355`（lab の profile、[13, 17] ℃、max_slew 5.0）

## 結果のまとめ

| id | 条件 | 状態 | 最初に検出した層 | V0 | V1 | V2 | V3 |
|---|---|---|---|---|---|---|---|
| U1 | `post-unit`（degF） | Tested | V3 | – | – | – | 検出 |
| U2 | `post-unit`（mK） | Tested | V3 | – | – | – | 検出 |
| U3 | `post-unit`（degR） | Tested | V3 | – | – | – | 検出 |
| M1 | `fail-missing-not-filled`（NaN） | Tested | V1 | – | 検出 | 検出 | 検出 |
| M2 | `fail-missing-not-filled`（+Inf） | Tested | V1 | – | 検出 | 検出 | 検出 |
| M3 | `fail-missing-not-filled`（値の無い frame） | Tested | V3 | – | – | – | 検出 |
| S1 | `fail-unverifiable-refused`（`dataType` を外す） | Tested | V3 | – | – | – | 検出 |
| S2 | 同上（`minValue` と `maxValue`） | Tested | V3 | – | – | – | 検出 |
| S3 | 同上（`maxValue`） | Tested | V3 | – | – | – | 検出 |
| R1 | `fail-release-failure-reported`（connector を外して解除） | Tested（試行 3） | V2 | – | – | 検出 | 検出 |
| R2 | 同上（plant を pause して解除） | Tested（試行 3） | – | – | – | – | **検出しない** |

- 集計（試行 3 の R1、R2 を入れたもの）：`artifacts/b12-summary-20261122b/results.json`（sha256 c7e26861…）。1 回目の集計
  `artifacts/b12-summary-20261121`（R1、R2 が Not Tested）は書き換えずに残す。
- Tested 11 件。V3 は 10 件を検出し、R2 だけ検出しなかった。V0 は 0 件、V1 は 2 件（M1、M2）、V2 は 3 件（M1、M2、R1）。
- 正常な入力での V3 の誤検出：97 / 102,567（0.095 %）（`artifacts/b12-normal-v3-20261121`、sha256 4d582789…）。
  内訳と、V0〜V2 の同じ入力での数は `artifacts/b11-contract-layers-20261121` と `docs/verification/2026-11-21-b11-contract-layers.md`。
- `fail-release-failure-reported` は R1 で発火した（V3 だけの条件として。最初の層は V2 の `post-default-readback`）。
  R2 では、注入が解除の失敗を作らなかった（遅れて効いた）。下の「試行 3」の節。

## telemetry の注入（U1〜U3、M1〜M3）

`artifacts/b12-telemetry-injection-20261121/results.json`（sha256 94957ed9…）。RI の部品を 1 process で動かした（事前登録 §3.3）。

## control の注入（S1〜S3）

| run | verify の結果（sha256） | verify の数 |
|---|---|---|
| S1 | `artifacts/b12-lab-run-b12-s1-20261121`（953cbcb5…） | Pass 143 / Fail 2 |
| S2 | `artifacts/b12-lab-run-b12-s2-20261121`（c97dcd0d…） | Pass 143 / Fail 2 |
| S3 | `artifacts/b12-lab-run-b12-s3-20261121`（0b381da8…） | Pass 143 / Fail 2 |

- Fail は 3 run とも `real_core_s3_history_*` の 2 件だけ（RI #657、cold reader が id で重複を除かない）。
- 3 run とも、twin の schema を欠いたまま RI は 15.0 の書込を受け付け（202）、readback は 15 だった。
  V3 の `fail-unverifiable-refused` だけがこれを flag する（V0〜V2 は flag しない）。

## R1、R2：試行 1、2 は Not Tested（Testbed の欠陥）、試行 3 で Tested

### 1 回目の試行（2026-11-21）：書込の前に止まった

- `artifacts/b12-lab-run-b12-r{1,2}-20261121.log`：verify の引数の検査が `--release-inputs` を approved の run にしか許さず、exit 2 で止まった。
  stack は起動せず、書込も無い。修正 eb1f514（`B3_RELEASE_RUNS`）。
- 事前登録 §6「環境の失敗（書込の前に止まった）は、新しい stack で 1 回だけやり直せる」に当たる。

### やり直し（2026-11-22、D=20261122）：書込の後に止まった

| run | verify の結果（sha256） | verify の数 | 時刻 |
|---|---|---|---|
| R1 | `artifacts/b12-lab-run-b12-r1-20261122`（25166f4a…） | Pass 101 / Fail 1（`execution`、KeyError） | 00:18:16Z〜00:22:36Z |
| R2 | `artifacts/b12-lab-run-b12-r2-20261122`（d83a01e2…） | Pass 101 / Fail 1（`execution`、KeyError） | 00:22:36Z〜00:27:04Z |

- 両方とも、Safety が 15.0 を承認し（approved）、RI が受け付け（202）、plant の priority 8 = 15.0 を読んだ
  （`artifacts/b12-lab-plant-b12-r{1,2}-20261122/priority-b12-before-release.json`）。
- その直後、`scripts/b3_lab/control_run.py` の R の段が `c["plant"]["plant_container"]` を読み、KeyError で止まった。
  `scripts/e2e03_lab/plant.py` の `require_owned_plant` が、`plant.json` のこの key を verify に渡していなかった。
  R の段は、これまで一度も live で走っていなかった。
- connector を外す、plant を pause する、解除する、のどれも行っていない。後片付けは Pass（`only_owned_cleanup`）。
- 事前登録 §6「書込の後の失敗は、やり直さずに報告する」により、**やり直さず Not Tested とする**。
- 欠陥の修正：9e6b540（`plant_container` を渡す。`tests/test_e2e03_require_owned_plant.py`）。

### 試行 3（2026-11-22、D=20261122b、補遺 r-retry）：Tested

補遺 `docs/preregistration/b12-v3-validation-addendum-r-retry.md`（dcb5168、run の前に commit）による 1 回だけのやり直し。
ユーザーの判断（2026-11-22）で行った。注入、`v3.py`、承認、Safety の材料は試行 2 と同じ。queue の log は `artifacts/b12-r-retry-20261122b.log`。

| run | verify の結果（sha256） | verify の数 | 時刻 |
|---|---|---|---|
| R1 | `artifacts/b12-lab-run-b12-r1-20261122b`（64cee061…） | Pass 148 / Fail 2 / Skip 0 | 01:23:34Z〜01:55:28Z |
| R2 | `artifacts/b12-lab-run-b12-r2-20261122b`（202c8694…） | Pass 148 / Fail 2 / Skip 0 | 01:55:28Z〜02:27:19Z |

- Fail は 2 run とも `real_core_s3_history_*` の 2 件だけ（RI #657）。後片付けは Pass。run の後、Testbed の container と network は残っていない。
- 書込：両方とも Safety approved、RI 202、RI の audit success、plant の priority 8 = 15.0（解除の前の読み）。

#### R1（connector を plant の network から外して解除）

| 時刻（Z） | 出来事 |
|---|---|
| 01:26:22 | 15.0 の書込（RI 202、connector `wrote analogValue,2=15.0 priority=8`） |
| 01:27:54 | priority 8 = 15.0、present value 15.0（`priority-b12-before-release.json`）。connector を外す |
| 01:27:59 | 解除：Safety approved、**RI 202**。RI の audit は 01:28:04 に `failed / timeout`、connector は 01:28:22 に `write timed out` |
| 01:29:30 | 外したままの読み：priority 8 = 15.0、present value 15.0（relinquishDefault 12.0） |
| 01:29:31 | connector をつなぎ直す |
| 01:31:02 | 戻した後の読み：priority 8 = 15.0 のまま。解除はやり直されず、plant に届かなかった |

- 判定（`control/b3/results.json`）：V2 `post-default-readback`、V3 `fail-release-failure-reported` と `post-default-readback`。最初の層は V2。
- 事前登録 §2 の (b)「2xx なのに、解除の後の配列が空でない」に当たる。HTTP の応答は 202 で、失敗は RI の audit（非同期の結果）にだけ出た。

#### R2（plant を `docker pause` して解除）

| 時刻（Z） | 出来事 |
|---|---|
| 01:58:12 | 15.0 の書込（RI 202） |
| 01:59:43 | priority 8 = 15.0。01:59:44 に plant を pause |
| 01:59:49 | 解除：Safety approved、**RI 202**。RI の audit は 01:59:54 に `failed / timeout`、connector は 02:00:11 に `write timed out` |
| 02:01:19.6 | plant を unpause。**同じ時刻（02:01:19.58）に plant が `command applied` 12.0**（relinquish）。sim は 94.9 s 遅れて再開した |
| 02:02:51 | 読み：配列はすべて空、present value 12.0 = relinquishDefault |
| 02:04:22 | 戻した後の読み：同じ |

- 判定：V0〜V3 のどれも検出しない。V3 の条件は HTTP の状態と解除の後の配列で決まり、どちらも「成功」だったからである。
- R2 は注入として解除の失敗を作らなかった。止めた plant に送った BACnet の書込は、再開の後に処理されて効いた
  （pause した container の UDP の受信は捨てられず、再開まで待つ、と読める）。事前登録 §4「検出できなかった注入も、そのまま報告する」により、検出しない、と数える。

#### 記録（判定しない）：R2 で、RI の記録と plant の状態が逆に食い違った

- RI の audit は解除を `failed / timeout`（5 s）と記録したが、plant では解除が効いた（約 90 s 後）。
- R1 は「202 なのに効いていない」、R2 は「audit は失敗なのに効いた」。どちらも、RI の応答や記録だけでは解除の結果が決まらず、
  plant の読み直しが要ることを示す。V3 の `fail-release-failure-reported` は前者だけを捉える。後者は、事前登録の条件の外にある。

## 制限

- `fail-release-failure-reported` は R1 の 1 件でしか発火していない（各注入 1 回）。R2 の形（遅れて効く解除）は条件の外。
- R1、R2 は試行 3 での結果である。試行 2 は書込の後の失敗で、§6 の文言では「やり直さない」に当たる。補遺 r-retry で、注入の前の Testbed の欠陥であることを根拠にやり直した。論文には試行 1〜3 をすべて書く。
- S1〜S3 は、7 つある部分集合のうち 3 つだけ（事前登録 §3.3、作者の選択）。
- telemetry の注入は RI の部品を 1 process で動かしたもので、Nexus からの経路ではない。
- BOPTEST は使っていない（hvac-sim の plant）。
