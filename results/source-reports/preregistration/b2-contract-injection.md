# B2：契約違反の注入と、検出率・誤検出の事前登録（#42）

この文書は、B3（#43）の注入を**実行する前に** commit する。結果を見た後に、注入の一覧、検出の数え方、指標、判定を書き換えない。変えるときは新しい文書にし、結果を見た後であることを書く（その解析は探索的と呼ぶ）。

- 論文：bde-paper `690ab81`。表 4（`tab:mismatch`、過去の不整合 14 件）と表 5（`tab:contract-spec`）。
- 契約試験一式：[`bos-contract-suite.yaml`](../../../src/bos_contract_testbed/data/bos-contract-suite.yaml)、`bos-contract-suite-v0`、sha256 `ce211aa48e98ee10f70dbe4b5874cd66a7b78c3dd2eed1af9fce4602843cc17e`（B1、#41）。
- 対象：RI `8c871466fff695761fcbedf52f1dcdb830f455db`（PX4 の pin）。T10 と T12 は gateway と仮想 BACnet 機器も含む。

## 1. 問いと仮説

- 問い（論文の RQ2、`tab:interop` の「契約違反の注入による検出率・誤検出」の行）：契約試験一式は、構造の検査だけでは見つからない違反を見つけるか。そのとき、正常な入力を誤って止めないか。
- 仮説 H：同じ注入の記録に 2 つの検査を当てると、次の 3 つがすべて成り立つ。
  1. 契約試験一式（C）が検出した注入の数は、構造の検査のみ（S）より多い。
  2. S が検出して C が見落とす注入は無い。
  3. 正常な入力の誤検出の割合は、C が S 以下である。

## 2. 構成

| 項目 | 値 |
|---|---|
| 検査の条件 | **S**：`bos-contract-suite.yaml` の `structure_only`。**C**：同じ定義の `operations`（下の §3.2） |
| 注入の対象 | RI `8c87146`。T10 と T12 は Nexus gateway と仮想 BACnet 機器（E2E-02 の構成）も含む |
| 書込の経路 | Safety Runtime だけ（§6 の D3）。注入の道具に書込の credential を渡さない |
| 正常な入力 | PX4 A run 2 と B run 1 の記録（§4） |
| BOPTEST | 使わない。時間の主体は要らない |
| 実行 | B3。L1 の構成を直列に走らせる。並列の agent からは走らせない |

## 3. 注入と検出

### 3.1 注入の一覧

各注入は 1 回ずつ行う。T は Testbed で行い、B3 で実行する。P は tenant-portal で行い、B4 で実行する。どちらも結果は別に報告する。

「表 4」の列は、再現しようとする過去の不整合を示す。区分の後の B は BDE、P は Portal で見つかったものである。

| id | 表 5 の行・セル | 注入 | 注入点 | 契約が求める振る舞い | 表 4 |
|---|---|---|---|---|---|
| T1 | 計測値の取得・Post | ℃ の Point に K の値（+273.15）を送る | gateway から RI ingress への telemetry frame | Point の定義の単位と違う値を検出する | 単位（B、P） |
| T2a | 計測値の取得・Pre | 登録済みの Point id の別の綴り（大文字と小文字を変える）で、最新値と履歴を読む | RI の読取 API | 契約の識別子空間に無い id を拒否する | 識別子（B） |
| T2b | 計測値の取得・Pre | 同じ別の綴りの id で telemetry frame を送る | RI ingress | 識別子空間に無い id の frame を拒否し、拒否を観測できる | 識別子（B） |
| T3 | 計測値の取得・Fail | 値の無い telemetry frame を送る | RI ingress | 欠測として区別し、0 で埋めない | — |
| T4 | 時刻・Pre と Post | 時計のメタデータ（`data` の `sim_clock_id`、`sim_time_quality` など）を除いた frame を送る | RI ingress | 出所の無い計測値を検出する | 時刻（B） |
| T5 | 時刻・Fail | sim 時刻が前の frame より戻った frame を送る | RI ingress | 巻戻りを品質で示し、アプリケーションが拒否できる | 時刻（B） |
| T6 | 書込・Fail | ControlSchema の下限より下の値を書く | Safety を通った RI の control API | 400 で拒否し、黙って丸めない | 制御（B）：10 ℃→12 ℃ |
| T7 | 書込・Pre | 読取だけの token で書く | RI の control API | 403 で拒否する | — |
| T8 | 書込・Fail | 書込の直前に、RI の ControlSchema を外す。既定（`CONTROL_SCHEMA_FAILURE_POLICY` を設定しない、allow） | RI の Point の metadata | 検証できないので拒否する | 制御（B）：検証の省略 |
| T9 | 書込・Fail | T8 と同じ。`CONTROL_SCHEMA_FAILURE_POLICY=deny` | 同上 | 同上 | 同上 |
| T10 | 書込・Post | 仮想機器が、受け付けた値と違う値を適用する（機器の側で上限に丸める） | 仮想 BACnet 機器 | 受付値と読戻し値の差を検出する | 制御（B）：読戻しが無い |
| T11 | 解除・T | 解除 Point に 0 を書く | Safety を通った RI の control API | 無効な値として拒否する | — |
| T12 | 解除・Fail | 書込の後、gateway を止めてから解除する | Nexus gateway | 失敗を返し、最後の値が残ることを知らせる | 制御（B）：見送り時に最後の値が残る |
| P1 | 認可付きの照会・T | 同じ利用者で、識別子の種類（sub と email など）を変える | tenant-portal | 判定が同じ | 認可（P）、識別子（P） |
| P2 | 認可付きの照会・T | 同じ権限を、別の表記で与える | tenant-portal | 判定が同じ | 認可（P）：権限の表記 |
| P3 | 認可付きの照会・T | 別の tenant と建物の資源を照会する | tenant-portal | 403 で拒否する | — |
| P4 | 認可付きの照会・Fail | 一括の照会に、権限の無い Point を混ぜる | tenant-portal | 部分的な失敗を 200 の成功に混ぜない | 失敗時の応答（P） |
| P5 | 認可付きの照会・Fail | BOS の認可判定を、timeout または 5xx にする | tenant-portal から BOS への経路 | 判定できないので拒否する | 認可（P） |

表 5 の 5 行のどれにも、注入が 1 つ以上ある。表 4 の制御の 4 件（丸め、読戻し、検証の省略、最後の値）は T6、T10、T8／T9、T12 に対応する。表 4 の認可の 4 件のうち、P1 と P2 と P5 に対応しない 1 件（サービスアカウントが管理者として扱われない）は、注入に含めない（§7）。

### 3.2 検出の数え方

1 つの注入につき、記録（trace）を 1 つ作る。trace に含めるのは、次の 3 つである。
- 注入の要求と応答（status、header、body）
- 注入の後に、同じ Point を読んだ最新値と履歴
- T10 と T12 では、読戻しと priority の配列

S と C は同じ trace を判定する。片方のために注入をやり直さない。

- **S（構造の検査のみ）：** `structure_only.counts_as_detected` のとおり数える。応答が RI `8c87146` の OpenAPI の schema に合わないか、2xx を期待した所で 2xx 以外が返れば検出である。telemetry の frame では、後で読んだ envelope の必須の欄（`device_id`、`point_id`、`value`、`datetime`）を見る。Point の読取で 2xx 以外が返れば検出とする。
- **C（契約試験一式）：** suite v0 で status が `covered` または `partial` の条件を、trace に当てる述語にする。1 つでも述語が成り立たなければ検出である。
  - `partial` の条件は、試験がある部分だけを述語にする。
  - `gap` と `conflict` の条件は、述語にしない。`conflict` の述語は、論文と逆を確かめているからである。
  - 述語は、suite に書いた試験 id の確かめ方に従う。B3 で述語のコードを書いたら、注入を始める前に commit し、その SHA を記録する。
- C で検出したときは、成り立たなかった述語の条件 id も記録する。それが注入の対象の行の条件か（対象の検出）、他の行の条件か（付随の検出）を分けて書く。主な指標では、どちらも検出に数える。
- **Safety が先に拒否したとき：** その注入では、RI に要求が届いていない。そのため S でも C でも Not Tested とし、「Safety の拒否」を参考の列に書く。
- 期待した応答を待つ時間は 120 s とする（transactions の `readback_s_bound` と同じ）。それまでに何も観測できなければ、その時点の trace で判定する。

### 3.3 結果を見る前の予想

予想は、suite v0 の status と RI `8c87146` の source から立てた。判定には使わない。

| id | S | C | 理由 |
|---|---|---|---|
| T1 | 見落とす | 見落とす | 値は数値で、schema に合う。`post-unit` は gap |
| T2a | 検出 | 検出 | 未知の id は 404 で返る見込み（`unknown_point_rejected`） |
| T2b | 見落とす | 検出？ | ingress は frame を捨て、読取は前の値を返す。C の `pre-id-space` の述語は、ingress の拒否を数える |
| T3 | 見落とす | 見落とす | RI は 0.0 にする。`fail-missing-not-filled` は conflict |
| T4 | 見落とす | 検出 | `data` は任意の欄である。`post-origin-and-quality` は covered |
| T5 | 見落とす | 検出 | 単調性の述語（`fail-quality-refusable` の covered の部分） |
| T6 | 検出 | 検出 | 400 |
| T7 | 検出 | 検出 | 403 |
| T8 | 見落とす | 見落とす | 既定は allow で、202 が返る。`fail-unverifiable-refused` は conflict |
| T9 | 検出 | 検出 | 400 |
| T10 | 見落とす | 検出 | 202 は正常である。`tb-transactions:match_rate` で検出する |
| T11 | 検出 | 検出 | 400 |
| T12 | 見落とす | 検出 | 解除は 202 を返す見込み。`post-default-readback`（priority の配列が空）で検出する。`fail-release-failure-reported` は gap なので、「失敗を返したか」は見ない |

予想どおりなら、検出は S が 5/13、C が 9〜10/13 になる。

## 4. 指標と判定

| 指標 | 式 | 母集団 | 単位 | 役割 |
|---|---|---|---|---|
| 検出率 DR_S、DR_C | 検出した注入 ÷ 判定できた注入 | T の 13 件。Not Tested は分母から除き、件数を書く | 1 | primary |
| 対の差 | C だけが検出した数 b、S だけが検出した数 c | T の 13 件 | 件 | primary |
| 誤検出の割合 FP_S、FP_C | 誤って検出した正常な入力 ÷ 判定できた正常な入力 | 下の 3 種。種ごとと合計 | 1 | primary |
| 行ごとの検出率 | 表 5 の行ごと | T | 1 | reference |
| 対象の検出の割合 | 対象の行の条件で検出した数 ÷ C の検出 | T | 1 | reference |
| P の検出率 | P1〜P5 で同じ式 | B4 の記録 | 1 | reference（別に報告する） |

**正常な入力**は、実際の記録の応答と行に、S と C の述語を当てたものである。正常な入力を RI に送り直すことはしない。

| 種 | 記録 | 件数（2026-11-08 に数えた） |
|---|---|---|
| 書込 | `artifacts/px4-a-run2-20261108/control/active-ledger.json`（sha256 `e9cb5bce…0456`）と `artifacts/px4-b-run1-20261108/control/active-ledger.json`（sha256 `36c09c18…651a`）で、dispatch が `ACCEPTED` の行 | A 161、B 672、計 833 |
| telemetry | 2 つの run の `telemetry/retrieved-*.parquet` の行 | A 137,410、B 25,149、計 162,559 |
| 解除 | 2 つの run の解除 | 2 |

- 書込で、記録に応答の body が無い行は Not Tested とする。検出しなかったことにはしない。
- telemetry の C の述語は、行ごとに当てられるものだけを使う。行をまたぐ単調性の述語は、Point と run ごとに当てる。

**判定**
- **pass：** H の 1〜3 がすべて成り立つ。
- **fail：** H のどれかが成り立たない。
- **inconclusive：** T の Not Tested が 3 件以上ある。または、正常な入力の Not Tested が、どれかの種で 10 % を超える。

数が少ないので、検定はしない。件数と割合だけを書く。

## 5. 止める条件

- 隔離を確かめられないとき。環境未準備と記録し、実行しない。
- §6 の D3 の承認が無いとき。T6、T8、T9、T11 は Not Tested とし、他の注入は続ける。
- 注入の後、承認された hard limit の外の値が設備（仮想機器）に適用されたとき。その場で解除し、止める。
- 実行中に RI、gateway、Safety の SHA または image が、記録と変わったとき。

## 6. 決めたこと（D 番号）と、その状態

- **D1（決めた）：** C は suite v0 を、この文書の sha256 のとおりに使う。B1 で gap だった 5 件の検査は、C に足さない。足した版を測るときは、新しい事前登録にする。
  - 理由：結果を見る前の suite を測るためである。gap を埋めた suite で測ると、作者が自分の試験に通る違反を選ぶ偏りが入る。
- **D2（決めた）：** S と C の違いは、検査だけである。注入、記録、時間の上限は同じにする。
- **D3（人の承認が要る）：** T6、T8、T9、T11 では、要求を RI まで届かせるために、lab だけの Point と lab の SafetyProfile と ControlSpec を使う。
  - 既存の承認済みの profile は変えない。注入の道具に、書込の credential を渡さない。
  - T6：lab の Point の RI ControlSchema を、Safety の hard limit より狭くする（例：Safety [21, 27]、RI [22, 26]、値 21.5）。Safety の hard limit は緩めない。
  - T8 と T9：Safety が schema の鮮度を確かめた後、書込の前に RI の schema を外す。それでも Safety が先に拒否すれば、§3.2 のとおり Not Tested にする。
  - T11：lab の解除 Point の Safety の許可に、0 を含める。この許可は lab の Point だけで、実際の解除 Point には付けない。
- **D4（決めた）：** P1〜P5 は B4 で行い、B3 の判定には入れない。

## 7. 結果を見る前に分かっている限界

- 注入の一覧も、検査の述語も、作者が作った。D1 と、この文書を先に固定することで、偏りを減らしているだけである。
- 注入は 1 件ずつである。検出率は割合というより、13 件の一覧として読む。
- 予想では、T1、T3、T8 は C でも見落とす。T1 は suite の gap、T3 と T8 は RI の既定が論文の Fail と逆であるためである。この 3 件は C の失敗ではなく、suite v0 と RI の現状の結果として書く。
- 誤検出の母集団は、PX4 の 2 つの run の記録だけである。Point も時間帯も限られる。
- 表 4 の「サービスアカウントが管理者として扱われない」は、注入に含めない。BOS の役割の割当の問題で、表 5 のどの条件の注入でもないからである。
- 論文の「越境・権限昇格 10 件」は、tenant-portal の `45c8297` で出所を確かめられていない（B1）。P3 で数え直す。
