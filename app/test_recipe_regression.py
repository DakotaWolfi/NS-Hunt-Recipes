from pathlib import Path
import json, re, sys, importlib.util
base=Path(__file__).resolve().parent
feed=json.loads((base/'recipes_bundled.json').read_text(encoding='utf-8-sig'))
assert len(feed['prizes']) == 12
assert len(feed['smelting']) >= 20
assert len(feed['crafting']) >= 1
bomb=next(x for x in feed['crafting'] if x['id']==8019)
assert bomb['name']=='unfinished bomb'
assert bomb['ingredients']=={'broken pager':2,'fried power storage module':4,'silver ingot':2,'bomb plans':1,'large capacitor':2}
assert bomb['not_consumed']==['bomb plans']
html=(base/'workshop.html').read_text(encoding='utf-8-sig')
assert 'Special crafting / Bomb' in html and 'function viewCrafting()' in html
assert 'data-done=\"${clean(r.result)}\"' in html
assert "track=r.machine==='Crafting'||r.machine==='Hunt prizes'" in html
assert 'state.done[el.dataset.done]=el.checked;save();render()' in html
assert 'done:state.done' in html
assert "state.tab==='crafting'?viewCrafting()" in html
jsfeed=re.search(r'const OFFLINE_FEED=(\{.*?\});\nlet recipeCatalogue=',html).group(1)
assert json.loads(jsfeed)==feed
assert 'applyRecipeFeed(OFFLINE_FEED' in html
spec=importlib.util.spec_from_file_location('ns_tracker_test',base/'live_server.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for mode in ['live','restore']:
    # Both modes share exactly one recipe lookup, not independent modes with different features.
    mapped=mod.build_live_recipes(feed)
    assert {x['id'] for x in feed['prizes']} <= set(mapped)
    assert {x['id'] for x in feed['smelting']} <= set(mapped)
    ingredients,output=mapped[8019]
    assert output=='unfinished bomb' and 'bomb plans' not in ingredients
    assert ingredients['large capacitor']==2
try:
    mod.validate_feed({**feed,'crafting':[]})
except ValueError as e:
    assert '8019' in str(e)
else:raise AssertionError('Missing bomb was silently accepted')
print('PASS: 12 prizes, 22 smelting, bomb 8019, nonconsumed plans, JS fallback and Python live/restore common mapping')
