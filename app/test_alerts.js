'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const page=fs.readFileSync(__dirname+'/workshop.html','utf8');
assert(page.includes("['alerts','🔔 Alerts']"));
assert(page.includes("state.tab==='alerts'?viewAlerts()"));
assert(page.includes('alertOnEvent(e,recipesBefore)'));
const source=page.split('// Alert preferences are browser-local')[1].split('const liveLog=[]')[0];
const seen=[];
const ctx={
 state:{stock:{'raw sapphire':0,'cut sapphire':0,'glass sheet':0},done:{},tab:'overview'},
 recipeCatalogue:[{id:8001,result:'Hunt Item 1',machine:'Hunt prizes',ingredients:{'raw sapphire':1,'glass sheet':1}},{id:8019,result:'unfinished bomb',machine:'Crafting',ingredients:{'cut sapphire':2}}],
 monitorMode:'live',avatarAccount:'jenna',avatarName:'Jenna',
 localStorage:{_data:{},getItem(k){return this._data[k]},setItem(k,v){this._data[k]=v}},
 window:{},document:{},console,Date,Set,JSON,
 clean:x=>x,render:()=>{},
};
vm.createContext(ctx);vm.runInContext('// Alert preferences are browser-local'+source+`\nalertPrefs.enabled=true;alertArmed=true;alertPrefs.items=['raw sapphire'];alertPrefs.recipes=['8001','8019'];\nfunction testEvent(e){const before=readySet();for(const [k,n] of Object.entries(e.delta||{}))state.stock[k]=(state.stock[k]||0)+n;alertOnEvent(e,before)}\n`,ctx);
vm.runInContext(`testEvent({kind:'loot',delta:{'raw sapphire':1}})`,ctx);
assert.equal(vm.runInContext('alertMessages.length',ctx),1);
assert.equal(vm.runInContext('alertMessages[0].kind',ctx),'loot');
vm.runInContext(`testEvent({kind:'loot',delta:{'glass sheet':1}})`,ctx);
assert.equal(vm.runInContext('alertMessages[0].kind',ctx),'ready');
assert.equal(vm.runInContext('alertMessages.length',ctx),2);
vm.runInContext(`testEvent({kind:'loot',delta:{'glass sheet':1}})`,ctx);
assert.equal(vm.runInContext('alertMessages.length',ctx),2,'No repeated recipe-ready ping');
vm.runInContext(`monitorMode='restore';testEvent({kind:'loot',delta:{'raw sapphire':1}})`,ctx);
assert.equal(vm.runInContext('alertMessages.length',ctx),2,'Historical restore silent');
vm.runInContext(`monitorMode='live';saveAlerts();avatarAccount='mel';loadAlerts()`,ctx);
assert.equal(vm.runInContext('alertPrefs.enabled',ctx),false,'Other avatar defaults disabled');
assert(vm.runInContext('alertPrefs.recipes.includes("8019")',ctx));
console.log('PASS: watched loot, ready transition, no duplicate alert, restore silent, avatar-specific settings');
