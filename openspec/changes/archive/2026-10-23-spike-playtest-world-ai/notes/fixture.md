# Fixture playtest-noai

Copy of the owner's slot saveGame_34 (saved 2026-10-23 17:21). Region Riesenbuckel. Files are in
`harness/fixtures/saves/playtest-noai/` on the main checkout (gitignored). The real files were only read.

Game settings: End goal Growth, AI opponents 0, Off map adversary Absent, Raider frequency None,
Initial bandit camps 0, Random bandit camp spawn limit 0, Spring, Standard supplies, No royal tax,
No armament delivery, Balanced residential, Standard spoilage, Low approval penalty, Underground water,
Difficult weather. Invasion Mod from main.

Proposed entry for `harness/fixtures/fixtures.json` (the implementation adds it):

```json
"playtest-noai": {
  "description": "The owner's playtest world (Riesenbuckel): AI opponents 0, Off map adversary Absent, Raider frequency None, Initial bandit camps 0, spawn limit 0, Invasion Mod from main. Only one coat file (_coat_0).",
  "origin": "user slot saveGame_34, playtest 2026-10-23",
  "sha256": {
    ".png": "7e779cb47a3969180ceef74f9c82c4472ac337373433fc35145e5734fe434cff",
    ".sav": "850bad328e76855b056003d046306ce1873648a886b3e5ec7cdec4839c6422b3",
    "_coat_0.png": "bcc5b7650f5c5f270ed58bc14d170a7db8ae1ffa1a38f3b58e8f1e5f11126d40",
    "_descr.sav": "0d866e295b3e2f4a567956f96f91493139d0896f7d16c24cbd0959d4d5927612"
  },
  "stored": true,
  "tags": ["playtest", "no-ai"]
}
```

Note: the hashes come from `sha256sum` of the copies. Check that the loader accepts a fixture with one coat file.
