NS Hunt Tracker v1.2.1 — live and historical restore
==================================================

PYTHON REQUIREMENT (WINDOWS)
----------------------------
Recommended: Python 3.12, 64-bit. A compatible Python 3 installation
with the Windows "py" launcher is required; Python 3.12 is not pinned.
Official download: https://www.python.org/downloads/windows/

During installation, include the Python Launcher ("py") and optionally
add Python to PATH. Check in Command Prompt: py -3 --version
The tracker uses only Python's standard library: no pip install needed.
Do not download or commit the Python installer into this repository.

NORMAL START:   START_HUNT.bat
FULL RESTORE:   RESTORE_HUNT.bat
UPDATE:         UPDATE_TRACKER.bat (or webpage Update tracker)

Both launchers run live_server.py; only startup parameters differ.
The app detects Firestorm accounts and reuses per-avatar saved inventories.
Restore replays existing chat logs; do not restore an already-correct inventory.

The updater repairs missing/stale launchers even at the same version and moves
obsolete START_*.bat scripts into legacy/ before they are removed from the
installation root. Inventories, log cursors, recipes cache, and settings are
never included in application releases or replaced by the updater.

For an old installation whose updater rejects newer manifest filenames, use the
one-time migration from the v1.2.1 release ZIP (copy UPDATE_TRACKER.bat and
update_tracker.py into the current application folder, then run UPDATE_TRACKER.bat
with the tracker stopped). Back up your app folder beforehand.

Developer tests: python test_updater.py; python test_startup.py;
python test_recipe_regression.py; node test_alerts.js.
Repo: https://github.com/DakotaWolfi/NS-Hunt-Recipes
