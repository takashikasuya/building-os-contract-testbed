# B13 シナリオ 4：解除の後に、低い優先度の値が有効になる（事前登録、#71）

この文書は、live の run を**始める前に** commit する。commit の後に、期待する動作、許容、止める条件、判定を書き換えない。

## 1. 問い

- BDE が priority 8 の書込を解除した後に、設備に別の writer の priority 16 の値が残っていたら、何が有効になるか。
- そのとき、今の検査はどう判定するか。対象は、verify の release の検査、C の `post-default-readback`、S である。
- 契約が「解除 = relinquishDefault に戻る」を前提にしているかを、観測で確かめる。

## 2. 構成

| 項目 | 値 |
|---|---|
| plant | PX5 と同じ。hvac-sim `64644ad`（image `building-os-e2e-hvac-sim:64644ad`、ID `326e92aa…`）、config `artifacts/px5-plant-config-20261107b/config.yaml`、1 倍速 |
| 経路 | PX5 と同じ。BDE `5f36355` の Safety → RI `8c87146` → Nexus → plant。configuration `px5-b-faults`、固定の提案（24.0、22.5、25.0、23.5 ℃ を各 10 周期）→ 人の指示の release |
| RI の実行用の image | `building-os-e2e-ri-runtime@sha256:f3b93cdf…`（PX5 の補遺 §8 と同じ） |
| Safety の承認 | `artifacts/b13-safety-inputs-unapproved-20261121`。human:<approver>、2026-11-21T13:46:36Z。PX5 の profile との違いは時刻だけ（規則は max_slew 2、stuck、override-detect で同じ） |
| 2 つ目の writer | PX5 F5 と同じ southbound の lab（NATS `ri609-nats-test@sha256:2ff72597…` と connector、自分の internal network）。`scripts/px5_lab/faults.py --fault p16` |
| 2 つ目の writer の動作 | 最初の提案から +600 s に、priority 16 に 26.0 ℃ を書く。+3000 s に解除する |
| 対象の object | `zone-101.temp-setpoint`（`analogValue,1`、relinquishDefault 28.0） |
| BOPTEST | 使わない |

- 26.0 は、BDE の 4 つの値と relinquishDefault（28.0）のどれとも違い、PX3 B の範囲（20〜26）の中にある。
- PX5 の F5 の run では、release は +2439 s、解除の後の priority の読取は +2530 s、終わりの読取は +2741 s だった。+3000 s は、その後に当たる見込みである。

## 3. 期待する動作

| # | 時点 | 期待 | 観測する物 |
|---|---|---|---|
| E1 | +600 s 〜 release の前 | priority 8 が BDE の値で、priority 16 が 26.0。present value は BDE の値（priority 8 が勝つ） | verify の `priority-before-release.json` |
| E2 | release の後（verify の解除の後の読取） | priority 8 は空、priority 16 は 26.0、present value は 26.0。relinquishDefault（28.0）ではない | `priority-after-release.json` |
| E3 | 同上 | verify の `release_priority_array_all_null` は **Fail**、`release_present_value_is_relinquish_default` も **Fail** の見込み（どちらも、writer が 1 つだけであることを前提にしている） | verify の results |
| E4 | 同上 | C の `post-default-readback` は flag を立てる見込み。S は flag しない見込み（解除の応答は 202） | 下の §5 の判定 |
| E5 | +3000 s の後 | 2 つ目の writer の解除の後、priority の配列はすべて空、present value は 28.0 | run の後に `plant.py priority` で読む |
| E6 | run の全体 | Safety の override-detect は、release の前には止まらない（priority 16 は 8 より低いので present value は変わらない） | Safety の ledger、監査 |

## 4. 判定

- **シナリオ 4 の観測は成立**：E1、E2、E5 がすべて成り立つ。
  - 値の許容は 1e-6（同じ値の読戻し）。
- **不成立**：E1、E2、E5 のどれかが成り立たない。
  - 例：release の後の present value が 28.0 になった（priority 16 が無視された）。
  - 起きたことを、そのまま報告する。
- E3、E4、E6 は判定に入れない。契約の観測できる範囲の所見として記録する。
  - 見込みと違っても、そのまま書く。
- verify の Pass／Fail の数は、E3 の 2 件が Fail になる見込みである。
  - RI #657 の既知の 2 件（timescale の cold reader）も Fail になりうる。B3 と PX5 で毎回出ている。
  - これらは原因ごとに分けて書く。

## 5. 検査の判定し直し（offline、run の後）

- run の記録から、B3 の `checks.py` の control の trace の形（`release_after` に、解除の後の priority の配列、present value、relinquishDefault）を作る。
- それに `s_flags` と `c_flags` を当てる。述語は変えない。
- trace を作る script は、run の後に書く。ただし、上の項目の対応を変えない。

## 6. 止める条件

- 承認の鮮度（2026-11-22T13:46:27Z）までに終わらない見込みのときは、始めない。
- plant が 2 つある、時間の主体が 2 つある、所有していない資源に触れそう、のどれかのときは止める。
- 2 つ目の writer の書込が、所有している plant 以外に向いたときは止める。
- 実設備や本番には向けない。2 つ目の writer に、BOS の書込の credential は渡さない（RI を通らない）。

## 7. やり直し

- 環境の失敗（image が無い、service が起動しない、書込の前に止まった）のときは、新しい bundle と plant で 1 回だけやり直せる。
- 書込の後の失敗は、やり直さずに報告する。

## 8. 限界

- 1 回だけの run である。
- B3（hvac-sim `2eb52e4`）と PX5／B13（`64644ad`）で、plant の SHA が違う。違いは watchdog（PX5 で足した物）で、この run の時間の中では効かない見込みである。それでも、論文では明記する。
- 2 つ目の writer は Testbed の lab であり、実際の BMS の別の writer の振る舞い（例：定期的に書き直す）は再現しない。
