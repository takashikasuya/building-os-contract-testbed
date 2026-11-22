# PX4 段 2 の補遺：B の live の RI の実行用の image を替える（run の前、2026-11-21）

この補遺は、B の live（`px4-s2-b-live-insitu`、`px4-s2-b-live-transferred`）を**走らせる前に** commit する。

## 1. 起きたこと

- 段 1 の B（`px4-b-run1-20261108`）と B3 は、RI を `bos-ri-main-building-os.api@sha256:ec20219d…` の上で動かした。
- この image は、2026-11-21 の時点で docker に無い。
  - PX5 の補遺 §8 と同じ理由で、ユーザーの `bos-ri-main` の作り直しで消えたものである。
  - local で作った image なので、registry から戻せない。
- このままだと、段 2 の configuration は bundle の `RI_RUNTIME_IMAGE`（`ec20219d…`）を使い、`ri-api` が起動しない。

## 2. 替える物

- PX5 と同じ `building-os-e2e-ri-runtime@sha256:f3b93cdf336dff0f6e92e12f3d680a32ef2c23bc0bd9d142bd1df9271c655d70` に替える。
  - 中身は `mcr.microsoft.com/dotnet/aspnet:8.0-noble-chiseled` で、dotnet は 8.0.34。
  - 2026-11-21 に、docker にあることを確かめた（local ID `f3b93cdf…`）。
- manifest の 2 つの configuration に `ri_runtime_image` を足す。`prepare_ri_provisioning_run.py` が bundle の値を置き換え、`results.json` に前後を書く。

## 3. 変わらない物

- この image で使うのは `/usr/bin/dotnet` だけである。RI `8c87146` の publish は、前と同じく read-only で mount する。
- BDE、Safety の材料、承認、plant、twin、PolicySpec、比べる相手の offline の手順は替えない。
- plant の image `building-os-e2e-hvac-sim:2eb52e4` は、同じ context から作り直した（manifest の `px4-b-px1-path.plant_image_deviation.rebuilt_again`）。中身の `site/` は替えていない。

## 4. 限界

- 段 1 の B と、段 2 の B の live では、RI の dotnet runtime の image が違う。段 1 の runtime の細かい版は記録が無い。
- 問い 2 の比べる相手は offline（plant と policy だけ）なので、RI の runtime の違いは入らない。live の結果と段 1 を比べるときは、この違いを書く。
