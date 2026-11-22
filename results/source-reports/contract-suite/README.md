# 契約試験一式（B1、#41）

論文 bde-paper の表 5（`tab:contract-spec`、契約の論理モデル C(o)=⟨Pre, Post, Fail, T⟩）について、試験一式を 1 つの定義に固定する。

- 定義（機械可読）：[`bos-contract-suite.yaml`](../../../src/bos_contract_testbed/data/bos-contract-suite.yaml)
- 対象：論文 `690ab81`、RI `8c871466fff695761fcbedf52f1dcdb830f455db`（PX4 の pin）
- 検査：`.venv/bin/python scripts/contract_suite.py [--out artifacts/<new>]`
  - 各条件に、試験か Gap があること。
  - Testbed の試験 id が、記録の results.json で Pass であること（A と B の両方）。
  - RI の試験 id が、RI `8c87146` の source にあること。
  - tenant-portal の試験 id は、この repo に source が無いので照合しない。
- 2026-11-08 の検査：`artifacts/b1-contract-suite-check-20261108/suite-check.json`。問題は 0。参照 66 件のうち 56 件を照合した。照合していない 10 件は tenant-portal のもの。

## 結果（35 条件）

表 5 の 5 行の各セルを、それ以上分けられない条件に分けた。

| 操作 | covered | partial | gap | conflict |
|---|---|---|---|---|
| 計測値の取得 | 3 | 1 | 2 | 1 |
| 時刻 | 3 | 1 | 2 | 0 |
| 書込（Control） | 8 | 2 | 0 | 1 |
| 解除（release） | 4 | 0 | 1 | 0 |
| 認可付きの照会 | 3 | 3 | 0 | 0 |
| **計** | **21** | **7** | **5** | **2** |

### conflict（試験はあるが、論文の条件と逆を確かめている）

1. **計測値の取得の Fail（欠測を 0 で埋めない）。**
   - RI の ingress は、値の無い frame を数値の 0.0 として受け付ける。古い gateway との互換のためである。
   - 試験 `GatewayIngressServiceTest.StreamTelemetry_NoValueCase_DefaultsToNumericZero` は、この振る舞いを確かめている。
2. **書込の Fail（検証できないときは拒否する）。**
   - RI の `CONTROL_SCHEMA_FAILURE_POLICY` の既定は allow で、試験もそれを確かめている。
   - 拒否は、deny を設定したときだけである。
   - 論文は既定が許容であることを書き、「既定で拒否」を本稿の提案（P）としている。

### gap（試験が無い）

1. 計測値が Point の定義の単位で返ること。
2. 単位の異なる値の注入。
3. 時計メタデータの欠落の注入。
4. 時計メタデータの巻戻りの注入（巻戻りは観測しているだけ）。
5. 解除の失敗（失敗を返し、最後の値が残ることを知らせる）。

### partial（一部だけ試験がある）

1. 識別子の別の綴り。未知の id だけを注入している。
2. 出所不明と巻戻りを品質で示し、アプリケーションが拒否できること。
3. 「受け付けた」と「適用した」の区別。
4. スキーマの欠落。deny の設定の、RI の単体の試験だけ。
5. 認可が判定できないときの拒否。権限の無い利用者の拒否だけで、BOS の障害は試していない。
6. 部分的な失敗を成功に混ぜないこと。batch-latest は、不可の Point を印なしで除く。
7. 権限の表記の違い。識別子の種類は試験がある。

### 出所と実行の範囲

- **Testbed の check**（`tb-verify`、`tb-ricontract`）：RI `8c87146` で実行した。PX4 の A run 2、B run 1、RI の component の契約 13 件。
- **E2E-02 の判定**（`tb-e2e02`）：Nexus と設備の層の試験で、RI の API の層ではない。
- **RI の単体の試験**（`ri-unit`）：source は `8c87146` にあるが、**Testbed では実行していない**（Not Tested）。
- **tenant-portal**（`tp`）：`45c8297`。
  - `authz-matrix.test.ts` は 68 件（`it()` 26 件と §2.1 の表の 42 件。2026-11-08 に数えた）。
  - 68/68 の記録は BOS `abf7aef`／`61d7ca6` に対するもので、RI `8c87146` では実行していない。
  - 論文の「越境・権限昇格 10 件」は、このファイルからは出所を確かめられなかった。

## 構造の検査のみ（B3 の比べる側）

定義は YAML の `structure_only` にある。

- RI `8c87146` の OpenAPI の schema（status の分類、必須の欄、JSON の型）と、telemetry の envelope の必須の欄だけで応答を検査する。
- 値、単位、時刻、事後の状態（読戻し、priority の配列）、監査、要求をまたぐ比較は見ない。

注入と指標は B2（#42）で事前登録した：[`b2-contract-injection.md`](../preregistration/b2-contract-injection.md)。2 つの条件の実行は B3（#43）で行う。
