#!/usr/bin/env python3
"""Publish ONLY program files to the app/ directory of the public recipe repository."""
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
from update_tracker import HERE,PROGRAM_FILES,MANIFEST
URL='https://github.com/DakotaWolfi/NS-Hunt-Recipes.git'

def main():
    listing={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in sorted(PROGRAM_FILES) if (HERE/name).is_file()}
    manifest={'schema':1,'version':'1.0.0','files':listing}
    (HERE/MANIFEST).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='ns_hunt_publish_') as tmp:
        root=Path(tmp)/'repo'
        subprocess.run(['git','clone','--depth','1',URL,str(root)],check=True)
        dest=root/'app';dest.mkdir(exist_ok=True)
        for name in listing:shutil.copy2(HERE/name,dest/name)
        shutil.copy2(HERE/MANIFEST,dest/MANIFEST)
        subprocess.run(['git','add','app'],cwd=root,check=True)
        if subprocess.run(['git','diff','--cached','--quiet'],cwd=root).returncode==0:
            print('Already published');return
        subprocess.run(['git','commit','-m','Publish NS Hunt Tracker v1.0.0'],cwd=root,check=True)
        subprocess.run(['git','push','origin','HEAD:main'],cwd=root,check=True)
        print('Published to https://github.com/DakotaWolfi/NS-Hunt-Recipes/tree/main/app')
if __name__=='__main__':main()
