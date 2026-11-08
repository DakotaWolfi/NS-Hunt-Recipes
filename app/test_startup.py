"""Offline startup tests: account saves, continue, fresh backup, no phantom stock."""
import tempfile, builtins, json
from pathlib import Path
import live_server as app

with tempfile.TemporaryDirectory() as td:
    root=Path(td);app.HERE=root
    p,f=app.prepare_inventory('Mel4anie','live','auto',root)
    assert f and p.name=='mel4anie.json' and json.loads(p.read_text())['stock']=={}
    app.atomic_json(p,{'stock':{'raw sapphire':7},'done':{'Hunt Item 1':True}})
    old=builtins.input
    try:
        builtins.input=lambda _:''
        resumed,f=app.prepare_inventory('Mel4anie','live','auto',root)
        assert not f and resumed==p and json.loads(p.read_text())['stock']['raw sapphire']==7
        builtins.input=lambda _:'n'
        fresh,f=app.prepare_inventory('Mel4anie','live','auto',root)
        assert f and fresh==p and json.loads(p.read_text())['stock']=={}
        assert len(list((root/'inventory_backups').glob('*.json')))==1
    finally: builtins.input=old
    restored,f=app.prepare_inventory('Mel4anie','restore','auto',root)
    assert f and restored.name=='mel4anie.restored.json' and restored!=fresh
print('PASS: no-save auto create; saved continuation; new backup; restore isolation')
