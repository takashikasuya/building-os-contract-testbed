# 事前登録の補遺：PX4 段 1、罰の重みの replay の手順（探索的）（2026-11-08）

**状態：確定（ユーザーの決定、2026-11-08。「model で回す」の案）。** [段 1 の事前登録](px4-stage1.md) の §2 の 5（罰の重みの選定）を具体にする。元の事前登録は変えない。探索的で、結果で合否は決めない。重みの選び方（§3）は変えない。

## なぜ足すか（結果を見る前に分かったこと）

- 元の事前登録は、replay で MPC に渡す前回の設定値を決めていなかった。
- `run_bde_pipeline.py` の driver は、replay の state に前回値を入れない。BDE の `l2replay.spread` は、前回値が無いと action の範囲の中央（24 ℃）を使う。
- ControlSpec の `rate_limit` は 0.5 ℃/周期なので、提案は必ず 23.5〜24.5 ℃になる。§3 の「内側の割合」（21.1 < u < 26.9）は、どの重みでも 1.0 になり、重みを選べない。
- 段 1 の学習（`artifacts/px4-{a,b}-train-20261108b`）の帯の replay（driver の既定の 4 つの帯）で、A と B の両方がこうなった。**重みごとの replay はまだ実行していない。**

## 手順

1. **model と dataset：** 段 1 の学習の出力（A：`artifacts/px4-a-train-20261108b`、B：`artifacts/px4-b-train-20261108b`）。dataset の窓は、事前登録の窓 [励起の開始, 開始 + 期間]（A は P2D、B は P7D）。学習は最初の 1.5 日／5 日、残りを holdout にする。
2. **重みの ControlSpec：** 帯の制約（`zone_temperature`、22〜24 ℃、soft）の `penalty` だけを 0.03／0.1／0.3／1.0 に置き換える。電力の下限の罰（100）、帯、`rate_limit`、id は変えない。A では、BDE の生成器（`prepare_excitation_approval_inputs.py --comfort-penalty`）で作った ControlSpec と、description 以外が同じであることを確かめる。
3. **開始の state：** holdout の行を、制御周期ごと（PT15M、grid の 3 行ごと）に取る。model の state（室温、冷房の電力、ファンの電力）と外気がすべてある行だけを使う。
4. **前回値：** その行の実際の設定値（dataset の `action_commanded__zone_cooling_setpoint`。applied が観測できないので、BDE の学習の view もこの列を使う）。無い行は使わない。
5. **回し方：** 学習した model と BDE の `LinearMPCPolicy` で 16 周期（4 h、MPC の horizon と同じ）回す。
   - MPC の呼び方は `l2replay.spread` と同じ。外気は開始の行の値のまま固定する。
   - 各周期で、提案 u を前回値にし、次の state を model の 1 歩（`model.step`）で作る。
6. **指標（重みごと、プラントごと）：**
   - **内側の割合（重みの選定に使う）：** 16 周期目の提案のうち、21.1 < u < 26.9 の割合。
   - 1 周期目の提案の内側の割合（参考）。
   - 帯の外：model が予測した室温が 22〜24 ℃の外にある量の、4 h の積分（K·h）。開始の state ごとの平均。
   - 提案の最小、最大、中央値。
7. **holdout の精度（§3）：** holdout の行で、model の 1 歩（15 分先）の予測と `<name>__next` の RMSE を、変数ごと（室温 K、冷房とファンの電力 kW）に出す。

## 重みの選び方（§3 のまま）

- 両方のプラントで、内側の割合（6 の 1 つ目）が 0.5 以上になる候補のうち、最も小さい重みを選ぶ。両方で同じ値にする。
- 当てはまる候補が無ければ、段 2 には進まず、目的を見直す。

## 結果を見る前に分かっている限界

- 外気は 4 h のあいだ固定する。日射と内部発熱は model の外にある。
- 回すのは学習した model の中だけで、プラントではない。プラントで張り付くかどうかは、段 2 の閉ループで確かめる。
- A の学習の最初の約 7.75 sim h は、Safety が拒否したので既定の制御（30 ℃）だった（励起の記録 (`../verification/2026-11-08-px4-stage1-excitation.md`, not exported)）。その行も学習に入っている。
