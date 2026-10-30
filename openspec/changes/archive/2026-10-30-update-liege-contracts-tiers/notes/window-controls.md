# Window controls (task 1.3)

The old pak widget (3 cards, active panel, arms button) did not fit the mockup, so the widget is rebuilt (`ue/make_liege_widget.py`) with the same method as the tech tree widget: one canvas of 1152 x 704, centred by the anchors of the seed widget.

Pools: 9 cards (`Card<r>_<c>` flat Border, texts `ReqLabel`, `ReqText`, `HaveText`, `RewLabel`, `RewText`, button Border `FulfilButton<r>_<c>`), 3 tier boxes (`TierName<r>`, `TierCount<r>`, a fixed "FULFILLED" label), header (`TitleText`, `RemainText`, `RefreshText`), `NoticeText` and a full-width `CloseButton`. No arms button, no influence or silver text. The pak must change: done. `WBP_LiegeContracts` is 23 KB (was 39 KB).

Build (verified): editor in a private UE workspace (copy of `ue/ManorLords.uproject` and the `Config` folder; the shared `mlm-ue` workspace was not used), `-ExecutePythonScript`, cook with `-run=cook -targetplatform=Windows -unversioned -nopak -skipeditorcontent` (exit 1 with unrelated "Content is missing" errors, the files exist), copy to `data/liege_contracts/assets/...`, `pakmod.py --config <private config> buildmod InvasionMod` with a private `work_dir` (the shared `modtools/work` build folder is wiped by `buildmod`; other agents may use it).

Trap: `run.py --pak InvasionMod` installs the pak from the `work_dir` of the pak config (`<work_dir>/out/InvasionMod_P.pak`), not from `mod/InvasionMod/paks/`. With the default config that is the shared folder, which can hold an old pak: the window then logs "class not found". Use `--pak-config` with the private config.

Picture check: the first picture (run 20261030-182223-1fa0) showed the two countdowns joined on one line; they are now on two lines.
