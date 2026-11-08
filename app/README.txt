NS HUNT TRACKER v1.0.0 — ONE APPLICATION / TWO MODES

Start with START_Live_Choose_Inventory.bat to select an existing inventory.
Start with START_Friend_Restore.bat to reconstruct from historical Firestorm logs.
Both use the same live_server.py, workshop.html, and GitHub recipe feed.

APPLICATION UPDATE
The webpage includes Check updates and Update tracker buttons. Update checks use:
 https://raw.githubusercontent.com/DakotaWolfi/NS-Hunt-Recipes/main/app/manifest.json
The stand-alone UPDATE_TRACKER.bat is the fallback (close the tracker first).
All downloaded source files are SHA256 checked against the manifest. Only known
program files are replaced; program_backups/ stores the prior version.
Inventories, Firestorm logs, state JSON, and recipes_cache.json are excluded.
The webpage update restarts the tracker in the same avatar/mode/inventory.

FIRST-TIME GITHUB PUBLICATION (ONE TIME)
The tracker application MUST be published to GitHub before either updater works.
This ZIP is not evidence that GitHub publishing already occurred.
1. Install Git for Windows, sign in with Git Credential Manager and set Git author
   name/email. Have push access to DakotaWolfi/NS-Hunt-Recipes.
2. Close the tracker and run PUBLISH_APP_TO_GITHUB.bat in this directory.
3. Verify https://github.com/DakotaWolfi/NS-Hunt-Recipes/tree/main/app
4. After that, future releases use the SAME publisher with an incremented
   application version in publish_app.py and a subsequent Git push.
The publication helper clones the recipe repository and commits ONLY whitelisted
application files into app/. No inventories, chat logs or credentials are published.
Recipe updates themselves remain separate and automatically refresh every 10 min.

SAFETY
Back up inventory JSON manually before the first migration. Do not run restore
against your working live inventory. Keep the GitHub repository trusted; app
updates execute local Python source. No updater can verify a publisher's intent.

TESTS
RUN_RECIPE_TESTS.bat checks recipes. Run `py -3 test_updater.py` for updater
checks. Real Windows/Firestorm integration still needs on-device testing.


v1.1 — Browser sound alerts
---------------------------
On the Alerts tab, enable sound alerts, adjust the volume, and click a Test
button once to unlock audio. Set individual watched loot names and toggle
recipe-ready notifications for hunt prizes and special crafting (bomb).
Defaults watch raw sapphire and cut sapphire and all prizes + bomb.
Loot ping is a short two-note sound; recipe-ready uses a three-note tune.
Alerts apply only to confirmed newly appended Firestorm loot while the browser
page is open and audio is unlocked. Historical restore is silent; inventory
imports, initial browser startup and manual stock edits do not ping.
Audio preferences are separate for each avatar/account and browser; the tracker
never uploads these settings to GitHub. App updates keep inventory files and logs.
