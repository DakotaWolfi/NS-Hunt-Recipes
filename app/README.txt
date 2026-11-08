NS HUNT TRACKER v1.2 — ONE APPLICATION, TWO LAUNCHERS

START_HUNT.bat   — Normal live tracker
RESTORE_HUNT.bat — Rebuild inventory from historical Firestorm chat logs

Both use live_server.py, workshop.html and the SAME GitHub recipe feed.

NORMAL STARTUP
1. The tracker discovers Firestorm account directories with chat-*.txt logs.
2. Choose the account if more than one exists.
3. If a saved inventory exists for the account, choose Continue (default)
   or New (start an empty inventory). Multiple matching saves are listed.
4. If no saved inventory exists, an empty JSON is created automatically.
5. Live mode skips old chat history when it has no prior cursor.

A new inventory is stored in inventories/<account>.json. Existing valid JSON
saves are reused in their original location; CSV files are converted to a
persistent .working.json next to the CSV. Never mix two avatars' files.
Choosing New backs up the existing save in inventory_backups/ before creating
an empty inventory. Associated old log cursors are backed up too.

RESTORE MODE
Historical restore uses the same application but its own separate state and
inventories/<account>.restored.json. Starting restore again backs up previous
restore output and rebuilds from available logs. This is an approximation:
trades and missing logs cannot be reconstructed automatically.

GITHUB UPDATES
The webpage has Check updates / Update tracker; UPDATE_TRACKER.bat is the
manual fallback (close running trackers first). Updates replace only program
files verified by SHA256, not inventories, log cursor files, or recipes cache.
Legacy launchers are archived in program_backups/ after updating to v1.2.
Keep backup copies of important inventories regardless.

ALERTS
The Alerts tab supports sounds, watchlist, recipe-ready notifications and volume.
Your browser needs a test-sound click to allow audio.

TESTS
RUN_RECIPE_TESTS.bat; py -3 test_startup.py; py -3 test_updater.py
