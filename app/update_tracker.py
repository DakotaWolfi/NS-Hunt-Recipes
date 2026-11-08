#!/usr/bin/env python3
"""Strict, stdlib-only updater. Updates program files, never inventories/logs/state."""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE='https://raw.githubusercontent.com/DakotaWolfi/NS-Hunt-Recipes/main/app/'
MANIFEST='manifest.json'
MAX_SIZE=2_000_000
PROGRAM_FILES={'live_server.py','workshop.html','recipes_bundled.json','test_recipe_regression.py',
 'RUN_RECIPE_TESTS.bat','START_HUNT.bat','RESTORE_HUNT.bat','README.txt',
 'update_tracker.py','test_alerts.js','test_updater.py','test_startup.py',
 'UPDATE_TRACKER.bat','PUBLISH_APP_TO_GITHUB.bat','publish_app.py'}
OBSOLETE_LAUNCHERS=('START_Choose_Avatar_Live.bat','START_Friend_Restore.bat',
 'START_Jenna_Live.bat','START_Live_Choose_Inventory.bat',
 'START_Live.bat','START_Restore.bat','START_Jenna_Live_v3.bat')

def download(name):
    with urllib.request.urlopen(urllib.request.Request(BASE+name,headers={'User-Agent':'NS-Hunt-Tracker-Updater/1.0','Cache-Control':'no-cache'}),timeout=12) as req:
        b=req.read(MAX_SIZE+1)
    if len(b)>MAX_SIZE:raise ValueError('Oversize update payload: '+name)
    return b

def remote_manifest():
    obj=json.loads(download(MANIFEST).decode('utf-8-sig'))
    if obj.get('schema')!=1 or not isinstance(obj.get('version'),str):raise ValueError('Invalid update manifest')
    files=obj.get('files')
    if not isinstance(files,dict) or not files or set(files)-PROGRAM_FILES:raise ValueError('Unrecognized application filenames')
    if not {'live_server.py','workshop.html','recipes_bundled.json','update_tracker.py'}<=set(files):raise ValueError('Incomplete update')
    if any(not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in files.values()):raise ValueError('Invalid file hash')
    return obj

def local_version():
    try:return json.loads((HERE/MANIFEST).read_text(encoding='utf-8')).get('version','unknown')
    except Exception:return 'unknown'

def needs_update(manifest):
    # Version alone is insufficient: launcher scripts can be absent or stale.
    if manifest['version'] != local_version():
        return True
    for name, expected in manifest['files'].items():
        path=HERE/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            return True
    # Also allow same-version cleanup of old launchers.
    return any((HERE/name).is_file() for name in OBSOLETE_LAUNCHERS)

def status():
    remote=remote_manifest()
    return {'current':local_version(),'latest':remote['version'],'available':needs_update(remote),'url':BASE}

def stage():
    manifest=remote_manifest()
    if not needs_update(manifest):return None,manifest
    temp=Path(tempfile.mkdtemp(prefix='ns_hunt_update_'))
    try:
        for name,expected in manifest['files'].items():
            payload=download(name)
            if hashlib.sha256(payload).hexdigest()!=expected:raise ValueError('SHA256 mismatch for '+name)
            (temp/name).write_bytes(payload)
        (temp/MANIFEST).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        return temp,manifest
    except Exception:
        shutil.rmtree(temp,ignore_errors=True)
        raise

def apply(stage_dir):
    stage_dir=Path(stage_dir).resolve()
    remote=json.loads((stage_dir/MANIFEST).read_text(encoding='utf-8'))
    if set(remote['files'])-PROGRAM_FILES:raise ValueError('Unsafe update paths')
    for name,h in remote['files'].items():
        if hashlib.sha256((stage_dir/name).read_bytes()).hexdigest()!=h:raise ValueError('Invalid staged '+name)
    # User information is never copied or erased. Only files on this allowlist are touched.
    backups=HERE/'program_backups'/time.strftime('%Y%m%d_%H%M%S')
    backups.mkdir(parents=True,exist_ok=True)
    replacing=list(remote['files'])+[MANIFEST]
    for name in replacing:
        if (HERE/name).exists():shutil.copy2(HERE/name,backups/name)
    completed=[]
    try:
        for name in replacing:
            os.replace(stage_dir/name,HERE/name)
            completed.append(name)
    except Exception:
        for name in completed:
            if (backups/name).exists():shutil.copy2(backups/name,HERE/name)
        raise
    finally:shutil.rmtree(stage_dir,ignore_errors=True)
    # Archive old launchers visibly. No user data is removed.
    legacy=HERE/'legacy'
    for filename in OBSOLETE_LAUNCHERS:
        old=HERE/filename
        if old.is_file():
            legacy.mkdir(exist_ok=True)
            dest=legacy/filename
            if dest.exists():
                dest=legacy/(old.stem+'_'+time.strftime('%Y%m%d_%H%M%S')+old.suffix)
            shutil.move(str(old),str(dest))
    return remote['version']

def wait_port_free(port,timeout=20):
    import socket
    for _ in range(int(timeout*10)):
        with socket.socket() as sock:
            sock.settimeout(0.3)
            if sock.connect_ex(('127.0.0.1',port))!=0:return
        time.sleep(.1)
    raise RuntimeError('Server still running; update canceled before modifying files')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--apply-stage');p.add_argument('--port',type=int,default=8765);p.add_argument('--restart-args',help='JSON array of args to restart the server');a=p.parse_args()
    if a.check:
        print(json.dumps(status(),indent=2));return
    if a.apply_stage:
        wait_port_free(a.port)
        version=apply(a.apply_stage)
        print('Updated to '+version)
        if a.restart_args:
            argv=json.loads(a.restart_args)
            if not isinstance(argv,list) or not all(isinstance(x,str) for x in argv):raise ValueError('Bad restart arguments')
            subprocess.Popen([sys.executable,str(HERE/'live_server.py'),*argv],cwd=str(HERE),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
        return
    staged,manifest=stage()
    if staged is None:print('Already current:',manifest['version']);return
    print('Downloaded and verified',manifest['version'])
    # The standalone updater is intended for a STOPPED tracker, to avoid replacing a running script.
    wait_port_free(8765,timeout=2)
    wait_port_free(8766,timeout=2)
    print('Installed',apply(staged))

if __name__=='__main__':
    try:main()
    except Exception as e:print('UPDATE FAILED:',e,file=sys.stderr);sys.exit(1)
