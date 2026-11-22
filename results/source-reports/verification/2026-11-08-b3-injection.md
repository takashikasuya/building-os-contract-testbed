# B3：契約違反の注入（#43、2026-11-08〜）

[事前登録](../preregistration/b2-contract-injection.md)（B2、sha256 `e7c910d6…0e79`）の実行の記録。

## 実行の前に決めたこと（結果を見る前に commit した）

検査の述語（`scripts/b3_lab/checks.py`）、正常な入力の評価（`scripts/b3_lab/normal.py`）、telemetry の注入（`scripts/b3_lab/telemetry_injection.py` と `telemetry/Program.cs`）は、注入も評価も走らせる前に commit した。

事前登録から外れる点は次の 3 つである。注入の一覧、検出の数え方、指標、判定は変えていない。

1. **実行の層。** 事前登録 §2 は「L1 の構成」としていた。telemetry の注入（T1、T2b、T3、T4、T5）は、RI `8c87146` の製品の部品を 1 つの process で動かして行う。
   - 使う部品は、ingress の中核（`GatewayIngressService`）、validated envelope、Hot store、Parquet の湖、query router、`TelemetryReading` DTO である。`tb-ricontract` と同じ作り方である。
   - gRPC の転送、mTLS、HTTP の認可（`AuthorizedTwinView`）は通らない。読取の status は、一覧を返す controller の 200 とする。
   - 理由：これらの注入で問うのは、RI が計測値をどう受け、どう返すかである。その処理は、この部品の中にある。
2. **T1 の向き。** PX4 A の provisioning の fixture には ℃ の Point が無い（温度はすべて K）。そこで、K の Point（室温 `BPT-0009`）に ℃ の値（22.0、295.15 K のつもり）を送る。違反の種類（Point の定義と違う単位の値）は同じである。
3. **T2a は後に回す。** T2a は読取の API で別の綴りの id を使う注入で、HTTP の認可の層を通さないと意味が無い。そのため、T6〜T12 と同じ L1 の実行で行う。

## 結果（telemetry の 5 件と、正常な入力。H の判定は末尾）

### telemetry の注入（`artifacts/b3-telemetry-injection-20261108b`）

- 述語を固定した commit は `bb42fa1` である。
- 最初の実行（`…20261108`）は build で止まった。`LakePartitionKey.For` の型の誤りで、注入は 1 件も走っていない。`f336662` で直してから実行した。
- RI は `8c87146` で、製品の部品を 1 つの process で動かした。image は実行していない。

| id | RI の振る舞い（trace で確かめた） | S | C | C の条件 |
|---|---|---|---|---|
| T1 | K の Point の ℃ の値 22 を受け付け、そのまま返す | 見落とす | 見落とす | — |
| T2b | 別の綴り `bpt-0009` の frame を捨てる。読取は空の一覧 | 見落とす | **検出** | `pre-id-space` |
| T3 | 値の無い frame を受け付け、**値 0 で返す**（RI #663） | 見落とす | 見落とす | — |
| T4 | 時計のメタデータの無い frame を、印なしで受け付ける | 見落とす | **検出** | `post-origin-and-quality` |
| T5 | sim 時刻が 3600 → 3000 に戻る 2 つの frame を、印なしで受け付ける | 見落とす | **検出** | `fail-quality-refusable` |

- 5 件とも、§3.3 の予想どおりである。
- C の検出は、3 件とも対象の行の条件による検出だった。
- S は 5 件とも見落とした。今回の S が見るのは読取の応答の構造だけで、5 件の読取はどれも 2xx の正しい形だった。

### 正常な入力の誤検出（`artifacts/b3-normal-20261108`）

| 種 | 件数 | S | C |
|---|---|---|---|
| 書込（dispatch が ACCEPTED） | 833（A 161、B 672。ledger の件数と一致） | 0 | 0 |
| telemetry の行 | 162,559（A 137,410、B 25,149） | 0 | 0 |
| 解除 | 2 | 0 | 0 |
| **計** | **163,394** | **0** | **0** |

- Not Tested は 0 件である。
- C の述語は、空振りではなく実際に当たっている。行の多くが `stable_unfenced` で sim 時刻を持ち、時計と巻戻りの述語の対象になった。`changed` の行は、sim 時刻が無くてよい規則で通った。
- 巻戻りのある Point は無かった。
- S は書込で、母集団の選び方（dispatch が ACCEPTED、つまり 202）から誤検出が 0 になる。これは測ったというより、定義から決まる。

## control 経路の設計（2026-11-09、実行の前に決めた）

T2a、T6〜T9、T11、T12 は、1 回の L1 の実行で、1 件ずつ順に行う。

- **構成：** PX4 B の plant（hvac-sim `2eb52e4`）、Nexus、RI `8c87146`、BDE `5f36355` の Safety Runtime。
- **lab の Point：** `ahu-1.sat-setpoint` を使う（ユーザーの決定、2026-11-09）。
  - この点は、PX4 B の使い捨て plant にある書込可能な BACnet の点で、analogValue 2、元の範囲は 12〜18 ℃。
  - 承認済みの Safety の profile は、どれもこの点を使っていない。
  - 解除点 `ahu-1.sat-setpoint.release` は、RDF の射影で足す。
  - mapping と注入の定義は `configs/proposals/b3-lab/` に置く。
- **T10：** E2E-02 の仮想 BACnet 機器に丸める挙動を足し、別に行う（ユーザーの決定、2026-11-09）。

### コードを読んで分かった制約

1. **Safety は、hard limit が焼き込んだ ControlSchema の内側にないと起動しない。**
   - 根拠は BDE `5f36355` の `SafetyRuntime._check_control_schema`。
   - Safety は、書込のたびに RI の schema を読み直すことはしない。
2. **RI は、解除点の schema が「enum で値 1 だけ」でないと、twin を取り込まない。**
   - 根拠は RI の `ReleaseOfIssueReasons.SchemaNotReleaseOnly`。
3. **RI の control API は、認可（403）→ schema の検証（400）→ gateway の未接続（503）→ 202 の順に判定する。**
   - 根拠は `PointController.Control`。
4. **lab の compose は `CONTROL_SCHEMA_FAILURE_POLICY: deny` に固定されている。**
5. **BDE の生成器は、SAT の一式を作れない。**
   - 給気温度の点（`equipment.ahu-1.t_supply_c`）が config に無いので、`--action sat` は `GenerateError` で止まる。
   - そこで lab の ControlSpec は、Testbed が書く。形と読込みは BDE のものに合わせる。これは E2E-03 と同じやり方である。

### 事前登録からの逸脱（結果の前に記録する）

4. **T6 のやり方。**
   - 事前登録 §6 の例は「Safety [21, 27]、RI [22, 26]」だった。しかし制約 1 があるので、Safety を RI より広くして承認することはできない。
   - そこで、Safety と RI を同じ [13, 17] で承認する。その後、注入として RI の twin の範囲だけを [14, 16] に狭め、13.5 を書く。
   - これは、Safety が焼き込んだ後に RI の schema が変わった状況である。
5. **T11 の Safety の許可。**
   - 制約 2 があるので、RI の解除点は {1} のままにする。
   - lab の解除の Safety の一式だけは、解除点の enum を {"0","1"} にした walk から焼く。
   - 実際の解除点（`zone-101.temp-setpoint.release`）には付けない。
6. **T8 の policy。** T8 の 1 件だけ、RI を `CONTROL_SCHEMA_FAILURE_POLICY=allow` で動かす。allow は RI の既定で、事前登録の T8 の条件である。他の注入は deny で行う。
7. **T12 の予想。**
   - 事前登録 §3.3 は、解除が 202 を返すと予想した。
   - 制約 3 から、gateway を止めると RI は 503 を返す見込みである。
   - 予想は直さない。結果は予想との違いとして書く。

8. **T2a を判定する C の条件（2026-11-09 に追加。control 経路の結果より前）。**
   - `checks.py` の `pre-id-space` は、送った frame しか見ていなかった。そのため、読取の API に別の綴りの id を渡す T2a は、事前登録 §3.3 の予想（C は検出する）を判定できなかった。
   - そこで、HTTP の trace が `id_space_reads` を立てたときだけ、登録に無い id の読取を flag する条件を足した。RI が拒否しても（拒否を観測）、答えても（違反）flag する。
   - component 層の trace（T1〜T5）はこの印を立てないので、判定は変わらない。記録済みの 5 件を判定し直し、S と C の結果が同じことを確かめた。
9. **T12 の「gateway を止める」の中身。**
   - Testbed が持つ egress の mTLS proxy を止める。これで、RI から見て gateway の egress の stream が無くなる。
   - Nexus と plant は動かしたままにする。proxy は T11 の後に起動し直す。

10. **T8 の読み戻し（2026-11-09、T8 の 1 回目の結果を見た後に決めた）。**
    - 1 回目（`artifacts/b3-lab-run-schema-removed-allow-20261109`）は、書込の 90 秒後に history（直近 30 分）だけで読み戻した。RI は 200 で空の一覧を返し、C は `post-readback` で「検出」した。同じ時刻の latest は、書込の後の値 15 を返していた。
    - RI の lake は Parquet への flush が 5 分ごとで、読み戻しは RI の起動から約 4 分後だった。history が空だったのは、flush の前だったためと見ている（tail merge が働かなかった理由は未確認）。
    - そこで T8 だけやり直す。90 秒後の読み戻しはそのまま残し、6 分後（flush の後）にもう一度読み戻す。読み戻した値には、両方の history の行と、書込より後の時刻の latest の行を数える。
    - これは結果を見た後の変更である。1 回目の結果も消さずに記録し、判定には 2 回目を使う。他の注入の手順と述語は変えない。

11. **T10 の注入点（2026-11-09、他の run の結果の後、T10 の実行の前に決めた）。**
    - 事前登録は「仮想機器が、受け付けた値と違う値を適用する（機器の側で上限に丸める）」とし、注入点を仮想 BACnet 機器とした。
    - hvac-sim `2eb52e4` は、範囲外の書込を必ず拒否し、値を丸めない（`runtime/write_gate.py`、`adapters/bacnet/command.py` の docstring）。product の repository は変えない。
    - そこで、Testbed が持つ BACnet/IP の中継（`scripts/b3_lab/clamp_relay.py`）を plant の network に置き、Nexus の connector の接続先を中継にする。中継は、`analogValue,2`（`ahu-1.sat-setpoint`）の presentValue への WriteProperty で、値が 16.0 より大きいときだけ 16.0 に書き換えて plant に渡す。plant の SimpleACK はそのまま返す。他の datagram（読取、解除、他の点）は byte のまま中継する。
    - 書く値は 16.5 とする。Safety の hard limit [13, 17] と RI の schema の内側なので、Safety と RI はそのまま通し、機器だけが 16.0 にする。
    - 読み戻しは、T8 と同じ数え方（逸脱 10）で、書込の後の latest と history を使う。BACnet の priority の配列も、plant から直接読んで trace に残す（判定には使わない）。
    - run は `clamp` を 1 つ足す（承認済みの twin、deny）。中継が T10 の書込だけを書き換えたことを、中継の log で検査する。

### RI 側の注入のやり方

- 承認済みの最終 RDF から、`injections.yaml` に書いた triple だけを変えた派生の twin を作る（`scripts/b3_lab/derive_twin.py`）。
- それ以外が変わっていないことは、triple の集合の差で確かめる。
- Safety の profile、hard limit、Deployment は、注入で変えない。
- **RI の twin は、実行の途中では変えない。** RI の metadata を変える製品の口は管理者用の取込 API で、lab の OIDC にはわざと管理者を置いていない。管理者の資格情報を足さないために、twin と policy の組ごとに、使い捨ての stack を 1 回ずつ立てる（4 回、manifest の `b3-lab-px4-b-path` の `runs`）。

| run | RI の twin | policy | 注入（この順） |
|---|---|---|---|
| approved | 承認済み | deny | T2a、T7、T12、T11 |
| narrowed | [14, 16] | deny | T6 |
| schema-removed-deny | schema なし | deny | T9 |
| schema-removed-allow | schema なし | allow | T8 |

- approved の run では、T12 を T11 より先に行う。RI が 400 を返すと、Safety はその点を止める（`ControlSchemaViolation` で suspend）ので、T11 を先にすると T12 の解除が Safety に拒否されてしまう。
- 道具：`scripts/b3_lab/control_run.py`（`verify_ri_provisioning.py --control-mode b3 --b3-run <run>`）、`injector.py`（1 手ずつの container）。bundle は `prepare_ri_provisioning_run.py --b3-twins --b3-variant --b3-policy` で作る。

### 事前の検査で分かったこと（未承認の mapping、offline）

- lab の Safety の材料は 17 Pass／0 Fail（`artifacts/b3-lab-safety-inputs-unapproved-20261109`）。
  - 13.5 と 15.0、解除の 0 と 1 は、承認した形の profile で、値のまま Safety を通る。
  - hard limit の外の値（12.5、17.5）を、Safety は拒否せず、上限か下限に丸めて通す（`projected`）。どの注入もこの値は使わない。Safety 自体が黙って丸めることは、表 4 の丸めの件と同じ形なので、結果の考察で触れる。

## control 経路の結果（2026-11-08〜09、L1、PX4 B の使い捨て plant）

承認：mapping 2 つ（human:<approver>、2026-11-08T20:20Z）、Safety の profile 2 つと Deployment 2 つ（同、20:26Z、24 時間有効）。実行はすべて期限の内側である。

### 実行の記録（失敗した実行も含む。結果の前に書く）

| 実行 | 結果 | 注入 | 原因と対応 |
|---|---|---|---|
| `…run-approved-20261109` | 46 Pass、2 Fail、約 15 秒で停止 | 走っていない | 環境の失敗。使った RI の build（`px4-ri-build-8c87146-20261108`）が、`0d38aca` より前の `CoreTelemetryAcceptance.cs` を記録しており、source の検査が止めた。同じ RI `8c87146` を今の source で build し直した（`b3-lab-ri-build-8c87146-20261109`、13 Pass）。`1187df8` |
| `…run-approved-20261109b` | 153 Pass、2 Fail | T2a、T7、T12、T11 | 判定に使う |
| `…run-narrowed-20261109` | 96 Pass、2 Fail、約 40 秒で停止 | 走っていない | Testbed の失敗。内側の gateway の lab の `real_ri_control_schema_is_the_approved_one` が、狭めた twin を拒否した。B3 の bundle のときだけ、「承認した mapping に宣言した注入の変更だけを加えたもの」と比べる検査に替えた（基準は下げない）。`88d5c37` |
| `…run-narrowed-20261109b` | 141 Pass、2 Fail | T6 | 判定に使う |
| `…run-schema-removed-deny-20261109` | 141 Pass、2 Fail | T9 | 判定に使う |
| `…run-schema-removed-allow-20261109` | 142 Pass、2 Fail | T8 | 逸脱 10 の前の読み戻し。C は `post-readback` で検出（history が空）。判定には使わない |
| `…run-schema-removed-allow-20261109b` | 143 Pass、2 Fail | T8 | 判定に使う（逸脱 10） |
| `…run-clamp-20261109` | 145 Pass、2 Fail | T10 | 判定に使う（逸脱 11）。中継の 3 つの検査は Pass（T10 の書込 1 件だけを 16.5→16.0 に書き換え、他の datagram は byte のまま） |

- 判定に使う 4 つの実行の 2 件の Fail は、どれも `real_core_s3_history_preserves_utc_values_data` と `real_core_s3_history_one_row_per_id` である。PX4 の run と同じ RI #657（timescale mode の cold reader が id で重複を除かない）。lab が使う lake の reader の 2 つの検査は Pass である。重複は窓の最初と最後の時刻だけで、注入の時刻とは重ならない。
- どの実行も、後片付け（`only_owned_cleanup`）は Pass である。

### 注入ごとの結果

| id | RI の振る舞い（trace で確かめた） | S | C | C の条件 | §3.3 の予想 |
|---|---|---|---|---|---|
| T2a | 別の綴り `AHU-1.SAT-SETPOINT` の latest と history に 403（正しい id は 200） | **検出** | **検出** | `pre-id-space` | 同じ（予想は 404） |
| T6 | Safety は 13.5 をそのまま通し、狭めた RI は 400（`value 13.5 is below the minimum 14`）。Safety は dispatch を `SCHEMA_VIOLATION` と記録 | **検出** | **検出** | `fail-out-of-range-refused` | 同じ |
| T7 | reader の token の書込に 403 | **検出** | **検出** | `pre-write-permission` | 同じ |
| T8 | schema なし、allow で 202（controlId あり、audit 1 行）。読み戻しは latest で 15 | 見落とす | 見落とす | — | 同じ |
| T9 | schema なし、deny で 400（`no_schema`） | **検出** | **検出** | `t-schema-missing` | 同じ |
| T11 | 解除 Point に 0 で 400 | **検出** | **検出** | `t-invalid-release-value` | 同じ |
| T10 | Safety は 16.5 をそのまま通し、RI は 202（audit 1 行）。中継が 16.0 に書き換え、plant の priority 8 と present value は 16.0。latest の読み戻しは 16 | 見落とす | **検出** | `post-readback` | 同じ |
| T12 | 15.0 の書込は 202。egress を切った後の解除は 503。BACnet の priority 8 に 15.0 が残る（present value 15.0、既定 12.0） | **検出** | **検出** | `post-default-readback` | **違う**：S は見落とす予想（解除が 202 の見込み）。503 は逸脱 7 の見込みどおり |

- Safety が拒否した注入は無い。どの注入も RI に届いた。
- T8 の history は、flush の後（書込の 7 分半後）も空だった。lab の ri-api には lake（MinIO）を渡しておらず（`api.env` は Postgres と NATS だけ）、HTTP の history には読む先が無い。latest は hot store から返る。RI の不具合ではなく lab の構成の限界なので、起票しない。approved の run で正しい id の history が 0 行だったのも同じ理由である。

## H の判定（T の 13 件）

| 指標 | S | C |
|---|---|---|
| 検出（判定できた 13 件） | 6（T2a、T6、T7、T9、T11、T12） | 10（T2a、T2b、T4、T5、T6、T7、T9、T10、T11、T12） |
| 検出率 | 0.46 | 0.77 |
| 誤検出（正常な入力 163,394 件） | 0 | 0 |

- Not Tested は 0 件。T10 は逸脱 11 の中継で行った（2026-11-09）。
- 対の差：C だけが検出 b = 4（T2b、T4、T5、T10）、S だけが検出 c = 0。
- H1（C の検出が S より多い）：10 > 6、成り立つ。H2（S が検出して C が見落とすものが無い）：c = 0、成り立つ。H3（誤検出の割合 C ≤ S）：0 ≤ 0、成り立つ。
- **判定：pass（13 件）。** T10 の前の 12 件での判定（pass）と変わらない。
- 対象の検出の割合：C の 10 件とも、注入の対象の行の条件による検出だった（10/10）。
- 予想（S 5/13、C 9〜10/13）との違い：S は T12 で 1 件多い。RI が gateway の未接続で 503 を返したからで、解除の失敗を status で返した。
- 考察で触れる点：Safety は hard limit の外の値を拒否せず丸めて通す（事前の検査で確かめた。どの注入もこの値は使っていない）。

## 残り

- **P1〜P5：** B4 で行った（記録 (`2026-11-09-b4-portal-injection.md`, not exported)、P の検出率は S 1/6、C 1/6）。
