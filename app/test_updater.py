"""Offline tests for update manifest, staging, hashes, data protection."""
import hashlib,json,tempfile
from pathlib import Path
import update_tracker as u

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp); source={'live_server.py':b'new server','workshop.html':b'new ui','recipes_bundled.json':b'{}','update_tracker.py':b'new updater'}
    manifest={'schema':1,'version':'1.2.0','files':{k:hashlib.sha256(v).hexdigest() for k,v in source.items()}}
    local=root/'install';local.mkdir(); (local/'inventory_Jenna.json').write_text('{"stock":{"x":5}}')
    (local/'live_state_Jenna.json').write_text('{"seq":200}')
    (local/'workshop.html').write_bytes(b'old ui')
    u.HERE=local
    u.download=lambda name: json.dumps(manifest).encode() if name=='manifest.json' else source[name]
    stage,info=u.stage();assert info==manifest
    assert u.apply(stage)=='1.2.0'
    assert (local/'inventory_Jenna.json').read_text()=='{"stock":{"x":5}}'
    assert (local/'live_state_Jenna.json').read_text()=='{"seq":200}'
    assert (local/'workshop.html').read_bytes()==b'new ui'
    assert (local/'program_backups').is_dir()
    assert u.stage()[0] is None
    bad={**manifest,'files':{**manifest['files'],'../inventory_Jenna.json':'a'*64}}
    u.download=lambda name:json.dumps(bad).encode()
    try:u.remote_manifest()
    except ValueError:pass
    else:raise AssertionError('Unsafe manifest accepted')
print('PASS: verified update, application backup, inventory/log state preservation, path whitelist')
