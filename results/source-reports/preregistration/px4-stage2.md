# 事前登録：PX4 段 2、方式の比較と移転の評価（確認的）（2026-11-10）

**状態：§8 の 1〜4 と 6 は人が決めた（2026-11-10、ユーザー）。** 残りは 2 つ。§8-5 の宣言（TTY の承認）と、§8-6 の pin の前の確認である。この commit の時点で、段 2 の run（offline の閉ループも含む）は 1 回も走らせていない。この後の変更は、新しい補遺に書く。

- 計画：PX4 の計画 (`../px4-plan.md`, not exported) の段 2、論文の計画 (`../paper-campaign-plan.md`, not exported) の PX4。
- 前の段：[段 1](px4-stage1.md)、[replay の補遺](px4-stage1-addendum-replay.md)、[段 1b](px4-stage1b.md)、[段 1 の解析と段 1b の結果](../verification/2026-11-08-px4-stage1-analysis.md)、移転の検査のやり直し (`../verification/2026-11-10-bde928-transfer-recheck.md`, not exported)。

## 1. 段 1 と段 1b から引き継ぐこと（事実）

- 学習データ：A run 2（BOPTEST、10 倍速、P2D）と B run 1（PX4 B の plant、60 倍速、P7D）。どちらも Safety の経路で集めた。
- model：段 1b の在室の時間帯（現地 8〜18 時）だけで学習した `linear_ssm`。定常の利得は A 0.69、B 0.93 K/K。
- **罰の重みは 0.3（人の判断、2026-11-08、結果を見た後）。**
  - 段 1b の §4 の規則では 0.1 が選ばれた。その判定は書き換えない。
  - 0.3 は、帯の外も基準に入れて選び直した値である。選び直しの規則は「内側の割合が両方のプラントで 0.5 以上、かつ各プラントの帯の外が候補の中の最小から 0.1 K·h 以内になる、最も小さい重み」。
  - この規則は段 1b の結果を見てから作った。論文には、その経緯を書く。
- 移転の検査：BDE `d46958f`（#929）の入力で、段 1 と段 1b の model の両方の向きが通った。作れたのは candidate の PolicySpec（署名なし）である。
- 学習の run の検査には `source_run_passed` の Fail が 1 件ある（RI #657、元の run の `real_core_s3_history_*` の 2 件）。BDE が学習に使う lake の reader の 2 件は Pass である。

## 2. 問い

1. **確認的：** 移した MPC とその場の MPC を、各プラントで live に 1 窓ずつ走らせたとき、Safety の違反は 0 か（4 回）。
2. **確認的：** live の 4 回の KPI は、同じ窓の offline の閉ループの KPI と、§5 の許容差の中で一致するか。
3. **報告だけ：** 5 つの方式を、2 つのプラントの 5 窓で offline に比べたとき、R_E、R_T、不快度の絶対差、日を単位にした対の差の 95 % CI はどうなるか。改善の幅は合否にしない。

## 3. 方式（各プラント）

| 方式 | 中身 | 通る経路 |
|---|---|---|
| 既定制御 | プラント自身の制御（BOPTEST は baseline、PX1 は hvac-sim の時刻表）。書込なし | offline だけ（P4-D4） |
| 規則の baseline | 冷房の設定値を **24 ℃** に固定（§8-3） | offline だけ（P4-D4） |
| その場の MPC | そのプラントの段 1b の model、重み 0.3 | offline と live |
| 移した MPC | 相手のプラントの段 1b の model を `transfer_policy.py build` で移したもの（重み 0.3 の ControlSpec に対して作り直す） | offline と live |
| 再学習した MPC | そのプラントの励起のデータのうち、最初の N 日の在室の時間帯だけで学習し直した model。N は A が 1、B が 1 と 7（P4-D3） | offline だけ |

- ControlSpec は、BDE の生成器の `--transfer-vars --comfort-band 22:24 --comfort-penalty 0.3` で作り直す（B は `--rate-limit 0.5` も付ける）。手では書き換えない。
- 移した MPC と再学習した MPC は、移転先の action の範囲（21〜27 ℃）と Safety profile で動く。

## 4. 窓と手順

### 窓
- **5 日：7 月 24、26、28、30 日、8 月 1 日**（§8-1）。各日の現地 13:00〜15:00（2 h、在室の時間帯の中）とする。
- 励起の期間と重ねない。段 1 の replay の state にも使っていない日である。
- 窓の前は、既定制御で窓の開始まで進める（BOPTEST の `warmup_period` にあたる）。

### offline（閉ループのハーネス、P4-D6）
- BOPTEST：BDE の `bde_testbed.boptest.closedloop`。`/advance` の刻みは live と同じにする（P4-D4）。
- PX1：`scripts/px4_lab/px1_closedloop.py`。
- 5 方式（再学習は B が 2 段）× 2 プラント × 5 窓。

### live（P4-D6）
- その場の MPC と移した MPC を、各プラントで 1 窓ずつ、合わせて 4 回行う。窓は §8-1 の 1 日目とする。
- 1 倍速で、Safety の経路を通す。直列で行う。各回は、Active 2 h、止めた後 15 min、release、観察 30 min とする（E2E-04 と同じ）。
- 承認：重み 0.3 の ControlSpec、Safety profile、Active の Deployment、移転の対応付けの宣言。live を行う日ごとに承認する（鮮度 24 h）。
- **学習の run の `source_run_passed` の Fail：** §8-4 の (a) で、予想した Fail として宣言した。

## 5. 指標と判定

### 確認的（合否）

| 問い | 合格の条件 |
|---|---|
| 1 | 4 回とも、Safety の判定の外の書込が 0、範囲と max_slew の違反が 0、止めた後の dispatch が 0 |
| 2 | 4 回とも、同じ窓の offline に対して、エネルギーが **±5 %** 以内、不快度が **±0.5 K·h** 以内（§8-2。E2E-04 の repeat と同じ許容差） |

- 1 回でも条件を外れたら、その問いは fail とする。止める条件（§6）で止まった回は inconclusive とし、合格には数えない。

### 報告だけ
- R_E：移した MPC のエネルギー ÷ その場の MPC のエネルギー（同じプラントの中の比、D8）。再学習した MPC も同じ比を出す。
- R_T：不快度の比。あわせて不快度の絶対差（K·h）も出す。
- 日を単位にした対の差（方式 − その場の MPC）の 95 % CI。t 分布で、n = 5 である。
- KPI の式は E2E-04 と同じ。
  - エネルギーは、冷房に関わる電力の台形積分（kWh）。A は FCU の冷房とファン、B は冷凍機と AHU のファン。
  - 不快度は、室温が目的の帯 22〜24 ℃の外にある量（K·h）。
  - BOPTEST の `tdis_tot`（BOPTEST 自身の快適域）は別に報告する。
- 室温と電力は、各プラントの Oracle から取る。BOPTEST は `/kpi` と同じ区間の積分、PX1 は `/export` と batch である。BDE の経路には入れない（N12 と同じ検査）。

## 6. 止める条件

- 承認から 24 h を過ぎた。
- 2 つ目の plant や時間の主体が現れた。
- plant、上位の SHA、producer の image が pin と違う。
- 実設備、本番、外部の network の兆候がある。
- 予想しない Fail が live の verify で出た（§8-4 で宣言した RI #657 の 2 件を除く）。

## 7. 結果を見る前に分かっている限界

- **プラントの設備が違う。** 対応付けでは同じ名前でも、中身が違う。
  - A の `cooling_power` は FCU の冷房、B は冷凍機である。
  - A の `fan_power` は FCU のファン、B は AHU のファンである。
  - そのため、エネルギーの比はプラントの中だけで作る（D8）。絶対値は比べない。
- model には時刻の入力が無い。窓は在室の時間帯の中に置いたが、時間帯の境界は仮定である（段 1b §5）。
- 重み 0.3 は、段 1b の結果を見た後に作った規則で選んだ（§1）。
- A の学習データは 2 日分で、再学習は 1 日分である。B の 7 日分とは量が違う。
- 方式の比較は、BOS と Safety を通らないハーネスで行う。経路を通したときの一致は、live の 4 回でだけ示す。
- A の開始の暦日は、BOPTEST の `time` の 0 を 1 月 1 日 0 時とした計算である（段 1 §7）。

## 8. 人の決定（2026-11-10、ユーザー。どれも推奨の案）

1. **評価の 5 日：決定。** 7 月 24、26、28、30 日、8 月 1 日。7 月 24 日〜8 月 6 日の候補から、1 日おきに機械的に選ぶ。天気を見て選ばない。live は 7 月 24 日。
2. **live と offline の許容差：決定。** エネルギー ±5 %、不快度 ±0.5 K·h（E2E-04 の repeat と同じ）。
3. **規則の baseline の固定値：24 ℃ に決定。** 計画は「上限に固定（26 ℃）」だったが、範囲を 21〜27 ℃に改訂した後、決め直していなかった。24 ℃ は（目的の帯の上端。快適性を保ちつつ電力を減らす運用の規則）。27 ℃（Safety の上限）にすると、快適性を捨てた比較になる。
4. **学習の run の `source_run_passed` の Fail：(a) に決定。** live の Active の署名は、B7-6 の規則のとおり、configuration に `expected_fail.checks` があるときだけ、この Fail を許す。
   - (a) PX4 の 2 つの configuration に `expected_fail.checks`（RI #657 の 2 件）を、段 2 の結果の前に宣言する。
   - (b) RI を、#657 を直した版に替え、学習データを集め直す。RI は今 develop の `81c4e3f` で、.NET 10 への移行と #664 も含む。
   - **(a) だけでは足りないことが分かった（2026-11-10、宣言の前）。** B7-6 の規則は、元の run の `results.json` に `real_core_lake_history_*` の 2 件が Pass で入っていることも求める。PX4 の A run 2 と B run 1 は、この 2 件ができる前の Testbed（`f8ec61a`）で走ったので、2 件が無い。
     - ユーザーの決定：2026-11-08 の offline の読直し（`artifacts/px4-history-reread-20261108`。保存した lake の object を、RI 8c87146 の `ParquetLakeTelemetryStore` で読み直したもの）を、manifest の `expected_fail.lake_history_reread` に sha256 で pin する。元の run に 2 件が無いときだけ、その pin で代える。
     - 規則の変更は `prepare_shadow_bundle.pipeline_fails_allowed`。2 件を記録している run には、今までどおり、その結果を使う。
     - 2026-11-10 に同じ道具で読み直し、A と B の結果は 11-08 のものと byte で同じだった。A は 137375 行、B は 25129 行で、期待と一致し、重複 id は 0。
5. **移転の対応付けの宣言（ADR-0017 D2）：前提を受け入れ、TTY の承認で宣言すると決定。** 宣言そのものは、まだ行っていない。今の対応付けは AI の下書きである。変数は 7 つで、役割、quantity kind、canonical unit、両側の点・source unit・PointKind がある。人が中身を確かめて、宣言として承認する。
   - 下書きの要約は 移転の対応付けの下書き (`../verification/2026-11-10-px4-transfer-mapping-review.md`, not exported) にある。
6. **BDE の pin：`d46958f` に決定。ただし下の 2 つを確かめてから替える。**移転の build と同じ版で、評価も行うためである。
   - `5f36355` から変わったのは 11 file である。
     - 移転の CLI と `transfer_inputs`。
     - 契約の `RewardTerm.regimes`。省略でき、既存の hash を変えない。
     - A の生成器の在室の regime。`occupancy` 引数で、既定は off。
     - BOPTEST の閉ループのハーネス（`closedloop.py`、+109 行）と、RL。
   - `src/bde/safety`、`services/`、依存は変わっていない。
   - pin を替える前に、2 つを確かめる。
     - 重み 0.3 の A と B の ControlSpec を、両方の版で生成し、byte で同じかを確かめる。
     - 閉ループのハーネスで、段 1b の model の既定の窓の結果が、両方の版で同じかを確かめる。
   - 違えば、その差を記録して、どちらの版にするかを人が決め直す。
