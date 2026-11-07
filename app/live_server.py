#!/usr/bin/env python3
"""Local-only incremental Firestorm log reader for Jenna. Python stdlib only."""
import argparse, csv, json, os, re, time, threading, webbrowser, uuid, shutil, urllib.request, subprocess, sys
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
DB = HERE / 'live_state.json'
LOOT = re.compile(r'\bYou found an? (.+?)\.$', re.I)
CRAFT = re.compile(r'\bCrafting (\d+)\.\.\.', re.I)
FAIL = re.compile(r'Crafting failed|crafting unsuccessful|could not craft', re.I)
END = re.compile(r'No longer crafting', re.I)
PREFIX = re.compile(r'^\[[^\]]+\]\s+([^:]+):\s+(.*)$')
ALIASES = {
 'bunch of fishy small capacitors':'fishy small capacitor bundle',
 'bunch of fishy medium capacitors':'fishy medium capacitor bundle',
 'bunch of fishy tiny capacitors':'fishy tiny capacitor bundle',
 'bunch of small capacitors':'small capacitor bundle',
 'bunch of medium capacitors':'medium capacitor bundle',
 'fishy giant capacitor':'fishy giant capacitor',
 'fishy large capacitor':'fishy large capacitor',
 'spent brass shell casing':'brass shell casing',
 'spent lead bullet tip':'lead bullet tip',
 "'disposable' e-vape":'disposable e-vape',
 'lump of glass slag':'lump of glass slag',
 'floopy disk':'floppy disk',
 'bunch of tiny capacitors':'tiny capacitor bundle',
 'bunch of large capacitors':'large capacitor bundle',
}
# Source recipe ingredients keyed to workshop inventory naming.
RECIPES = {
 8001:({'roll of cabling':6,'555 timer':4,'empty aerosol can':8,'cracked circuit board':3,'bronze ingot':4}, 'Hunt Item 1'),
 8002:({'small capacitor bundle':3,'vacuum tube':2,'oscillator':3,'gold ingot':2,'cut diamond':2}, 'Hunt Item 2'),
 8003:({'servo':2,'box of cereal':3,'aluminum ingot':5,'glass sheet':5}, 'Hunt Item 3'),
 8004:({'lump of electrolytic paste':6,'leaky battery':6,'busted car gps':2,'cut sapphire':2}, 'Hunt Item 4'),
 8005:({'tiny tuna':4,'disposable e-vape':1,'seaweed clump':6,'orange soda can':2,'box of cereal':1}, 'Hunt Item 5'),
 8006:({'servo':2,'roll of electrical tape':1,'bronze ingot':1,'cut quartz':3,'lead ingot':3}, 'Hunt Item 6'),
 8007:({'medium capacitor bundle':2,'length of copper wiring':4,'tv remote':2,'broken pager':2,'glass sheet':6}, 'Hunt Item 7'),
 8008:({'giant capacitor':1,'cassette tape':1,'oscillator':2,'busted car gps':3,'steel ingot':3}, 'Hunt Item 8'),
 8028:({'fishy small capacitor bundle':1,'lump of electrolytic paste':2},'small capacitor bundle'),
 8029:({'fishy medium capacitor bundle':1,'lump of electrolytic paste':2},'medium capacitor bundle'),
 8031:({'fishy giant capacitor':1,'lump of electrolytic paste':1},'giant capacitor'),
 8027:({'fishy tiny capacitor bundle':1,'lump of electrolytic paste':2},'tiny capacitor bundle'),
 8030:({'fishy large capacitor':1,'lump of electrolytic paste':1},'large capacitor bundle'),
 4001:({'raw sapphire':1},'cut sapphire'),4002:({'raw diamond':1},'cut diamond'),4003:({'raw quartz':1},'cut quartz'),
 5004:({'length of copper wiring':5},'copper ingot'),
 5005:({'message in a bottle':1},'glass sheet'),
 5006:({'empty aerosol can':5},'aluminum ingot'),
 5007:({'empty soda can':5},'aluminum ingot'),5008:({'orange soda can':5},'aluminum ingot'),
 5009:({'lump of pure silicon':1},'glass sheet'),5010:({'lump of glass slag':1},'glass sheet'),
 5011:({'copper node':1},'copper ingot'),5012:({'gold nugget':1},'gold ingot'),
 5013:({'piton':4},'steel ingot'),5014:({'brass shell casing':6},'bronze ingot'),
 5015:({'lead bullet tip':6},'lead ingot'),5016:({'iron lump':1},'iron ingot'),
 5017:({'bauxite clod':1},'aluminum ingot'),5018:({'tin can':3},'tin ingot'),
 5019:({'scrap of lead shielding':6},'lead ingot'),
 5020:({'handful of loose screws':5},'steel ingot'),
 5021:({'coal lump':2,'iron ingot':2},'steel ingot'),
 5022:({'copper ingot':1,'tin ingot':1},'bronze ingot'),
 5023:({'set of broken subcutaneous arm plates':1},'steel ingot'),
 5024:({'set of broken subcutaneous leg plates':1},'copper ingot'),
 5025:({'silver ore':1},'silver ingot'),
 7023:({'corrupted eeprom chip':1},'blank eeprom chip'),
 7024:({'blank eeprom chip':1},'disk controller eeprom'),
 8025:({'action figure':1},'inaction figure'),
 8026:({'copper ingot':1},'length of copper wiring'),
}

# Single shared source for restore/live, crafting, and browser UI.
RECIPE_URL='https://raw.githubusercontent.com/DakotaWolfi/NS-Hunt-Recipes/main/recipes/recipes.json'
RECIPE_CACHE=HERE/'recipes_cache.json'
RECIPE_BUNDLED=HERE/'recipes_bundled.json'
recipe_meta={'status':'Bundled offline snapshot','last_check':0,'error':None}
recipe_lock=threading.RLock()

def validate_feed(data):
    if not isinstance(data,dict) or data.get('schema_version') != 1:raise ValueError('Unsupported recipe schema')
    if not isinstance(data.get('prizes'),list) or not isinstance(data.get('smelting'),list):raise ValueError('Missing prizes/smelting')
    if len(data['prizes'])<12:raise ValueError('Unexpectedly incomplete prize list')
    if not any(x.get('id')==8019 for x in data.get('crafting',[])):raise ValueError('Missing bomb recipe 8019')
    if len(data['smelting'])<20:raise ValueError('Unexpectedly incomplete smelting list')
    for entry in data['prizes']+data['smelting']+data.get('crafting',[]):
        if not isinstance(entry.get('id'),int) or not isinstance(entry.get('ingredients'),dict):raise ValueError('Invalid recipe')
        if any(not isinstance(n,int) or n<0 for n in entry['ingredients'].values()):raise ValueError('Invalid recipe quantities')
    return data

def build_live_recipes(data):
    result=dict(RECIPES)
    for entry in data['prizes']+data['smelting']+data.get('crafting',[]):
        required=set(entry.get('not_consumed',[]))
        ing={k.lower():v for k,v in entry['ingredients'].items() if k not in required}
        result[entry['id']]=(ing,entry.get('name') or f"Recipe {entry['id']}")
    return result

def activate_feed(data, status):
    global current_feed, RECIPES
    data=validate_feed(data)
    with recipe_lock:
        current_feed=data
        RECIPES=build_live_recipes(data)
        recipe_meta['status']=status;recipe_meta['error']=None
    print('Recipe source:',status,'|',data['catalog_version'],'| prizes:',len(data['prizes']),flush=True)

activate_feed(json.loads(RECIPE_BUNDLED.read_text(encoding='utf8')),'Bundled GitHub snapshot')
if RECIPE_CACHE.exists():
    try:activate_feed(json.loads(RECIPE_CACHE.read_text(encoding='utf8')),'Cached GitHub recipes')
    except Exception as exc:print('Recipe cache invalid, keeping bundled snapshot:',exc,flush=True)

def refresh_feed():
    recipe_meta['last_check']=time.time()
    try:
        request=urllib.request.Request(RECIPE_URL,headers={'User-Agent':'NS-Hunt-Tracker/0.9','Cache-Control':'no-cache'})
        with urllib.request.urlopen(request,timeout=7) as stream:
            if stream.headers.get('Content-Length') and int(stream.headers['Content-Length'])>2000000:raise ValueError('Recipe feed too large')
            raw=stream.read(2000001)
        if len(raw)>2000000:raise ValueError('Recipe feed too large')
        data=validate_feed(json.loads(raw))
        activate_feed(data,'GitHub live feed')
        atomic_json(RECIPE_CACHE,data)
        return True
    except Exception as exc:
        recipe_meta['error']=str(exc)
        print('GitHub refresh failed, keeping existing recipe catalog:',exc,flush=True)
        return False

def recipe_monitor():
    while True:
        refresh_feed()
        time.sleep(600)

# File-backed inventory: selected JSON is editable; selected CSV gets a JSON
# sidecar so completed prizes and event cursor are not lost.
def choose_inventory(option, account):
    if option == 'none': return None
    if option and option not in ('ask','auto'):
        selected=Path(os.path.expandvars(option)).expanduser().resolve()
        if not selected.is_file():raise SystemExit('Inventory file not found: '+str(selected))
    else:
        roots=[HERE, HERE/'inventories', Path.cwd()]
        candidates=sorted({p.resolve() for root in roots if root.is_dir() for pat in ('*Inventory*.json','*Inventory*.csv','*inventory*.json','*inventory*.csv') for p in root.glob(pat) if not p.name.startswith('live_state') and not p.name.startswith('restore_state') and not p.name.endswith('.backup.json')})
        print('\nExisting inventory files:',flush=True)
        for i,path in enumerate(candidates,1):print(f' {i}. {path.name} [{path.parent}]')
        if option=='auto' and len(candidates)==1: selected=candidates[0]
        else:
            print(' Enter file number, or paste an absolute path to an existing .json/.csv file.')
            print(' 0 = new empty inventory (NOT Jenna screenshot estimates).')
            while True:
                answer=input('Inventory file: ').strip().strip('"')
                if answer=='0':return None
                if answer.isdigit() and 1<=int(answer)<=len(candidates):selected=candidates[int(answer)-1];break
                path=Path(os.path.expandvars(answer)).expanduser()
                if path.is_file():selected=path.resolve();break
                print('Choose a listed number or existing file path.')
    if selected.suffix.lower()=='.csv':
        sidecar=selected.with_name(selected.stem+'.working.json')
        if sidecar.exists():print('Using existing working copy:',sidecar,flush=True)
        else:
            with selected.open('r',encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f)
                if not {'item','quantity'}.issubset(set(reader.fieldnames or [])):
                    raise SystemExit('CSV requires item and quantity columns')
                rows=list(reader)
            content={'stock':{r['item'].strip().lower():max(0,int(float(r['quantity'] or 0))) for r in rows if r.get('item')},'verified':{r['item'].strip().lower():str(r.get('verified','')).strip().lower() in ('yes','true','1') for r in rows if r.get('item')},'done':{},'source_csv':str(selected)}
            atomic_json(sidecar,content)
            print('Imported CSV once and created a persistent working JSON:',sidecar,flush=True)
        return sidecar
    if selected.suffix.lower()!='.json':raise SystemExit('Select a .json or .csv inventory')
    return selected

def atomic_json(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temp,path)

def inventory_snapshot():
    if not inventory_file:return None
    obj=json.loads(inventory_file.read_text(encoding='utf-8-sig'))
    if not isinstance(obj,dict) or not isinstance(obj.get('stock'),dict):
        raise ValueError('Inventory JSON must contain a stock object')
    return obj

lock=threading.RLock()

def load():
    if DB.exists():
        try:
            d=json.loads(DB.read_text(encoding='utf-8'))
            if isinstance(d.get('offsets'),dict) and isinstance(d.get('events'),list): return d
        except Exception as e: print('Could not read state:',e)
    return {'offsets':{},'events':[],'seq':0,'pending':None,'fresh':True}
state=load()
state.setdefault('session', str(uuid.uuid4()))
state.setdefault('mode', 'live')

def persist():
    temp=DB.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2),encoding='utf-8');os.replace(temp,DB)

def event(changes,kind,detail):
    state['seq']+=1
    state['events'].append({'seq':state['seq'],'delta':changes,'kind':kind,'detail':detail})
    print(f"[{state['seq']}] {kind}: {detail}",flush=True)

def canon(raw):
    k=raw.strip().strip('.').lower()
    return ALIASES.get(k,k)

def finalize_pending():
    p=state.get('pending')
    if not p: return
    state['pending']=None
    if p.get('failed'): return
    recipe=int(p['recipe'])
    if recipe not in RECIPES:
        event({},'unmapped_craft',f'Recipe {recipe} not in recipe table; no inventory change')
        return
    ingredients, output=RECIPES[recipe]
    delta={k:-v for k,v in ingredients.items()}
    if recipe==7024: delta['program for disk controller firmware']=0 # reusable tool is not consumed
    if output.startswith('Hunt Item '):
        event(delta,'prize',f'{output} (recipe {recipe})')
    else:
        delta[output]=delta.get(output,0)+1
        event(delta,'craft',f'{recipe}: {output}')

def consume_line(s):
    m=PREFIX.match(s.strip())
    if not m:return
    sender,body=m.group(1),m.group(2).strip()
    if sender in ('TSX-11Y','Geode','bobber'):
        loot=LOOT.search(body)
        if loot:
            state['last_loot']=canon(loot.group(1))
            return
        if body=='It has been added to your inventory.' and state.pop('last_loot',None):
            # The previous item must be remembered across descriptions, so see pending below.
            return
        if body.startswith('You let it go.') or body.startswith('You feel closure.'):
            state.pop('last_loot',None)
        return
    if sender.startswith('Invent Trader'):
        c=CRAFT.search(body)
        if c:
            finalize_pending()
            state['pending']={'recipe':int(c.group(1)),'failed':False}
        elif FAIL.search(body):
            if state.get('pending'):state['pending']['failed']=True
        elif END.search(body):finalize_pending()

def process_text(line):
    """Credit only an explicitly confirmed find; descriptions may be unprefixed."""
    raw=line.strip()
    if raw=='It has been added to your inventory.':
        item=state.pop('last_loot',None)
        if item:event({item:1},'loot',item)
        return
    if raw.startswith(('You let it go.','You feel closure.')):
        state.pop('last_loot',None)
        return
    m=PREFIX.match(raw)
    if not m:return
    sender,body=m.groups();body=body.strip()
    if sender in ('TSX-11Y','Geode','bobber'):
        found=LOOT.search(body)
        if found:state['last_loot']=canon(found.group(1))
    elif sender.startswith('Invent Trader'):
        consume_line(raw)

def tick(folder):
    with lock:
        files=sorted(folder.glob('chat-*.txt'))
        if not files:return
        if state.pop('fresh',False):
            if state.get('mode') == 'live':
                for p in files:state['offsets'][str(p.resolve())]=p.stat().st_size
                print('First run: existing chat contents skipped. Watching NEW lines only.',flush=True)
                persist();return
            print('Historical restore: reading available chat logs from the beginning.',flush=True)
        for p in files:
            key=str(p.resolve());size=p.stat().st_size
            if key not in state['offsets']:state['offsets'][key]=0 # new daily log
            pos=state['offsets'][key]
            if size<pos:pos=0;state['last_loot']=None;state['pending']=None
            if size==pos:continue
            with p.open('rb') as f:
                f.seek(pos);raw=f.read()
            lines=raw.splitlines(keepends=True);complete=[];advanced=0
            for b in lines:
                if b.endswith((b'\n',b'\r')):
                    complete.append(b.decode('utf-8',errors='replace'))
                    advanced+=len(b)
                else:break
            for l in complete:process_text(l)
            state['offsets'][key]=pos+advanced
        persist()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
        if urlparse(self.path).path=='/app/update':
            import update_tracker
            try:
                staged,manifest=update_tracker.stage()
                if staged is None:
                    payload=json.dumps({'status':'current','version':manifest['version']}).encode()
                    self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
                restart=['--log-dir',str(log_dir),'--mode',args.mode,'--inventory',str(inventory_file) if inventory_file else 'none','--avatar',avatar_name,'--port',str(args.port)]
                helper=[sys.executable,str(HERE/'update_tracker.py'),'--apply-stage',str(staged),'--port',str(args.port),'--restart-args',json.dumps(restart)]
                subprocess.Popen(helper,cwd=str(HERE),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
                payload=json.dumps({'status':'restarting','version':manifest['version']}).encode()
                self.send_response(202);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);self.wfile.flush()
                threading.Thread(target=lambda:(time.sleep(.25),server.shutdown(),server.server_close()),daemon=True).start()
            except Exception as ex:self.send_error(502,str(ex))
            return
        if urlparse(self.path).path=='/recipes/refresh':
            success=refresh_feed()
            self.send_response(204 if success else 503);self.end_headers();return
        if urlparse(self.path).path!='/inventory' or inventory_file is None:
            self.send_error(404);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<2000000:raise ValueError('Invalid size')
            obj=json.loads(self.rfile.read(length))
            if not isinstance(obj,dict) or not isinstance(obj.get('stock'),dict):raise ValueError('Missing stock')
            with lock:
                existing=inventory_snapshot()
                # Preserve extra custom fields carried in JSON backups.
                existing.update({k:obj[k] for k in ('stock','verified','done','liveSeq','monitorSession') if k in obj})
                atomic_json(inventory_file,existing)
            self.send_response(204);self.end_headers()
        except Exception as exc:
            self.send_error(400,str(exc))
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/app/version':
            import update_tracker
            try:payload=update_tracker.status()
            except Exception as ex:payload={'current':update_tracker.local_version(),'latest':None,'available':False,'error':str(ex)}
            data=json.dumps(payload).encode();mime='application/json'
        elif u.path=='/recipes':
            with recipe_lock: payload={'feed':current_feed,'status':recipe_meta['status'],'error':recipe_meta['error'],'url':RECIPE_URL,'checked_at':recipe_meta['last_check']}
            data=json.dumps(payload).encode();mime='application/json'
        elif u.path=='/events':
            cursor=int(parse_qs(u.query).get('after',['0'])[0]);
            with lock: payload={'events':[e for e in state['events'] if e['seq']>cursor],'latest':state['seq'],'folder':str(log_dir),'account':log_dir.name,'avatar':avatar_name,'mode':state['mode'],'session':state['session']}
            data=json.dumps(payload).encode();mime='application/json'
        elif u.path=='/inventory':
            with lock:
                payload={'inventory':inventory_snapshot(),'path':str(inventory_file) if inventory_file else None,'baseline_seq':starting_seq,'account':log_dir.name}
            data=json.dumps(payload).encode();mime='application/json'
        elif u.path in ('/','/workshop.html'):
            data=(HERE/'workshop.html').read_bytes();mime='text/html; charset=utf-8'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

def monitor():
    while True:
        try:tick(log_dir)
        except Exception as e:print('Monitor issue:',repr(e),flush=True)
        time.sleep(0.35)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--log-dir',default='auto');parser.add_argument('--port',type=int,default=8765);parser.add_argument('--mode',choices=['live','restore'],default='live');parser.add_argument('--reset-restore',action='store_true');parser.add_argument('--avatar',default=None,help='Display name of the Firestorm avatar');parser.add_argument('--inventory',default='none',help='ask, auto, none, or a .json/.csv path')
    args=parser.parse_args()
    if args.log_dir.lower() == 'auto':
        base=Path(os.environ.get('APPDATA',str(Path.home()))) / 'Firestorm_x64'
        choices=sorted(p for p in base.iterdir() if p.is_dir() and list(p.glob('chat-*.txt'))) if base.is_dir() else []
        if not choices: raise SystemExit('ERROR: No Firestorm account directories containing chat-*.txt in '+str(base))
        if len(choices)==1: log_dir=choices[0]
        else:
            print('Choose the Firestorm avatar log folder:')
            for i,p in enumerate(choices,1): print(f' {i}. {p.name}')
            while True:
                try:
                    n=int(input('Account number: '))
                    if 1<=n<=len(choices): break
                except (ValueError,EOFError): pass
                print('Select a listed number.')
            log_dir=choices[n-1]
    else: log_dir=Path(os.path.expandvars(args.log_dir)).expanduser()
    avatar_name=args.avatar.strip() if args.avatar else log_dir.name
    DB=HERE / ('restore_state_'+re.sub(r'[^a-zA-Z0-9_-]','_',log_dir.name)+'.json' if args.mode=='restore' else 'live_state_'+re.sub(r'[^a-zA-Z0-9_-]','_',log_dir.name)+'.json')
    if args.reset_restore and args.mode=='restore' and DB.exists():
        DB.rename(DB.with_suffix('.backup.json'))
    state=load();state.setdefault('session',str(uuid.uuid4()))
    if not state.get('offsets') and not state.get('events'):
        state['mode']=args.mode;state['fresh']=True
    if state.get('mode') != args.mode:
        raise SystemExit('ERROR: Existing state mode is different. Use separate launchers/state files.')
    if not log_dir.is_dir():raise SystemExit(f'ERROR: Firestorm account log folder not found: {log_dir}')
    inventory_file=choose_inventory(args.inventory,log_dir.name)
    if inventory_file:
        # Check selected inventory before starting monitor; don't mutate original by scanning history.
        inventory_snapshot()
        print('WORKING INVENTORY:', inventory_file, flush=True)
    else: print('No selected inventory file; using browser-local inventory.',flush=True)
    starting_seq=state['seq']
    print('Watching:',log_dir,flush=True);print('Open: http://127.0.0.1:%d/'%args.port,flush=True)
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    threading.Thread(target=recipe_monitor,daemon=True).start()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    webbrowser.open('http://127.0.0.1:%d/'%args.port)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
