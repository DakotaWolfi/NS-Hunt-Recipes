# Nanite Systems Hunt 26 — public recipe feed

Public, **recipe-only** data feed for the local [NS Hunt Tracker](https://github.com/DakotaWolfi/NS-Hunt-Recipes). No player data or Firestorm logs are stored here.

**Live JSON:** https://raw.githubusercontent.com/DakotaWolfi/NS-Hunt-Recipes/main/recipes/recipes.json

The tracker downloads this JSON on startup and checks for updates approximately every 10 minutes, keeping the last valid copy for offline use. Weekly additions require editing the JSON here, not redistributing the client.

## Current coverage

- Hunt 26 prizes **8001–8012** (12 prizes, first two weeks).
- Capacitor repairs, smelting/conversion planning, and **22 numbered Smelter recipes (5004–5025)**. The workshop displays these in a separate Smelter tab.
- Optional 8019 (unfinished bomb) is listed separately from Hunt prizes.
- Recipe **8012** needs a tech fossil but **does not consume** it. Recipe **8019** needs bomb plans but does not consume them.
- Non-consumed items are recorded in `not_consumed` arrays.

## Weekly maintenance

1. Edit `recipes/recipes.json`.
2. Add verified new entries under `prizes`, keyed by real numerical recipe IDs.
3. Increase `catalog_version` and set `updated_at`.
4. Commit. The local clients will fetch the new catalogue automatically.

The file uses schema version **1**. Please do not add invented ingredient lists. Item names should match the canonical names used in the tracker.

## Privacy and security

Only public recipe definitions belong in this repository. **Never upload personal inventory exports, local state JSON, avatar data, logs, or access tokens.**
