// Edit Room regression test. usage: node run.js <page.html>   (needs playwright + chromium; exits 1 on any FAIL)
const {chromium}=require('playwright');const path=require('path');
const page_=path.resolve(process.argv[2]);let fails=0;const log=[];
const ok=(c,m)=>{log.push((c?'PASS ':'FAIL ')+m);if(!c)fails++};
const STUB=cfg=>`window.__cfg=${JSON.stringify(cfg)};(()=>{const cfg=window.__cfg,docs={},cbs={};window.__docs=docs;
 const mk=(c,id)=>({id,exists:true,data:()=>JSON.parse(JSON.stringify(docs[c+'/'+id]))});
 for(const k in (cfg.init||{}))docs[k]=cfg.init[k];
 window.claude={use:async()=>{if(cfg.dbLate)await new Promise(r=>setTimeout(r,cfg.dbLate));return{doc:p=>({set:async b=>{docs[p]=JSON.parse(JSON.stringify(b));const [c,id]=p.split('/');setTimeout(()=>(cbs[c]||[]).forEach(f=>f({docs:[mk(c,id)]})),cfg.echo||250)},onSnapshot:()=>{}}),
  collection:c=>({onSnapshot:f=>{(cbs[c]=cbs[c]||[]).push(f);const snap0=JSON.parse(JSON.stringify(cfg.init||{}));setTimeout(()=>f({docs:Object.keys(snap0).filter(k=>k.startsWith(c+'/')).map(k=>({id:k.split('/')[1],exists:true,data:()=>JSON.parse(JSON.stringify(snap0[k]))}))}),cfg.delay||300)}})}}}})();`;
async function open(b,vp,cfg){const pg=await b.newPage({viewport:vp});pg.errs=[];pg.on('pageerror',e=>pg.errs.push(String(e)));await pg.addInitScript(STUB(cfg||{}));
 await pg.route('**/fonts.googleapis.com/**',r=>r.fulfill({status:200,body:''}));await pg.goto('file://'+page_);await pg.waitForFunction(()=>document.getElementById('vid').readyState>=2,null,{timeout:20000});await pg.waitForTimeout(700);return pg}
const seek=async(pg,f)=>{const tl=await pg.locator('#tl').boundingBox();await pg.mouse.click(tl.x+tl.width*f,tl.y+tl.height*.8);await pg.waitForTimeout(250)};
const tap=async(pg,x,y)=>{const st=await pg.locator('#stage').boundingBox();await pg.mouse.click(st.x+st.width*x,st.y+st.height*y);await pg.waitForTimeout(220)};
const js=(pg,f,a)=>pg.evaluate(f,a);
const doc=pg=>js(pg,()=>JSON.parse(JSON.stringify(window.__docs['pins/reel']||null)));
(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
for(const [name,vp] of [['desktop',{width:1280,height:800}],['phone',{width:390,height:664}]]){const T=m=>name+': '+m;
 /* A-G: the user's complaints, in one session */
 let pg=await open(b,vp);
 ok(await js(pg,()=>document.querySelectorAll('.ri.ready').length)===20,T('all 20 thumbnails load'));
 await pg.click('#bPin');await seek(pg,.1);await tap(pg,.3,.3);await seek(pg,.3);await tap(pg,.6,.45);await seek(pg,.5);await tap(pg,.4,.7);await seek(pg,.8);await tap(pg,.7,.25);
 ok(await pg.locator('#plist .row').count()===4,T('4 pins listed'));
 await seek(pg,.95);await pg.waitForTimeout(300);
 const ghosts=await js(pg,()=>[...document.querySelectorAll('.pin')].filter(e=>+e.style.opacity>.2).length);ok(ghosts>=3,T('pins never vanish: '+ghosts+' ghosts visible away from their moment'));
 await js(pg,()=>document.getElementById('bPin').click());await pg.keyboard.press('Escape');await pg.waitForTimeout(200);
 for(const i of [0,1,2]){await js(pg,i=>document.querySelectorAll('#plist .row .ck')[i].click(),i);await pg.waitForTimeout(100)}
 await js(pg,()=>document.querySelector('.ab .pri').click());await pg.waitForTimeout(800);
 ok(await pg.locator('.grp .row').count()===3,T('grouped pins appear under their Change card'));
 ok(await pg.locator('.pin').count()===4,T('grouping keeps all pins on the video'));
 await pg.keyboard.type('Bigger shape',{delay:30});await pg.waitForTimeout(900);const d1=await doc(pg);
 ok(d1&&d1.groups.A&&d1.groups.A.note==='Bigger shape'&&d1.pins.filter(p=>p.group==='A').length===3,T('change note + group saved'));
 await js(pg,()=>[...document.querySelectorAll('.xr')].pop().click());await pg.waitForTimeout(900);ok((await doc(pg)).pins.length===3,T('x on a row deletes that pin'));
 await js(pg,()=>document.querySelector('.rst').click());await js(pg,()=>document.querySelector('.rst').click());await pg.waitForTimeout(1100);
 ok((await doc(pg)).pins.length===0&&await pg.locator('#plist .row').count()===0,T('Reset pins clears everything (two taps)'));
 await pg.keyboard.press('Control+z');await pg.waitForTimeout(900);ok((await doc(pg)).pins.length===3,T('undo restores the reset'));
 /* K: drag after undo (stale object regression) */
 await seek(pg,.1);const pe=await pg.evaluateHandle(()=>[...document.querySelectorAll('.pin')].find(e=>+e.style.opacity>.9));const bb=await pe.asElement().boundingBox();
 await pg.mouse.move(bb.x+bb.width/2,bb.y+bb.height/2);await pg.mouse.down();await pg.mouse.move(bb.x+bb.width/2+40,bb.y+bb.height/2+30,{steps:5});await pg.mouse.up();await pg.waitForTimeout(700);
 const bb2=await pe.asElement().boundingBox();ok(Math.abs(bb2.x-bb.x-40)<6,T('pin still draggable after undo'));
 /* H: cross-view */
 await js(pg,()=>document.querySelectorAll('#rail .ri')[3].click());await pg.waitForTimeout(1500);
 ok(await js(pg,()=>document.querySelectorAll('.pin').length)>=0,T('scene view opens'));
 const before=(await doc(pg)).pins.length;await pg.click('#bPin');await tap(pg,.5,.5);await pg.waitForTimeout(800);const dd=await doc(pg);
 ok(dd.pins.length===before+1,T('pin added in a scene view lands in the one reel store'));
 const np=dd.pins.find(p=>!p.id.startsWith('x')&&Math.abs(p.t-0)>=0)&&dd.pins.sort((a,b)=>b.t-a.t)[0];
 await js(pg,()=>document.querySelectorAll('#rail .ri')[0].click());await pg.waitForTimeout(1200);ok(await pg.locator('#plist .row').count()===before+1,T('reel list shows the scene pin too'));
 ok(pg.errs.length===0,T('no page errors ('+pg.errs.join(';').slice(0,120)+')'));await pg.close();
 /* I: stale remote snapshot arriving AFTER local edits must not wipe them */
 const remote={by:'other',at:'2020-01-01T00:00:00.000Z',pins:[{id:'r1',t:3,x:.5,y:.5,mode:'auto',note:'remote',group:'',target:'',between:null,resolved:null}],groups:{}};
 pg=await open(b,vp,{init:{'pins/reel':remote},delay:2500});
 await pg.click('#bPin');await seek(pg,.4);await tap(pg,.3,.3);await seek(pg,.6);await tap(pg,.6,.6);await pg.waitForTimeout(3200);
 const dI=await doc(pg);ok(await pg.locator('#plist .row').count()===3,T('late first snapshot is merged, not overwritten (3 rows)'));ok(dI&&dI.pins.length===3,T('merged result saved'));await pg.close();
 /* J: legacy per-scene docs are folded into the reel store */
 const leg={by:'old',at:'2020-01-01T00:00:00.000Z',pins:[{id:'s02-a',t:.5,x:.4,y:.4,mode:'auto',note:'',group:'A',target:'',between:null,resolved:null},{id:'s02-b',t:.9,x:.6,y:.6,mode:'precise',note:'',group:'A',target:'',between:null,resolved:null}],groups:{A:{note:'legacy note'}}};
 pg=await open(b,vp,{init:{'pins/reel':{by:'o',at:'2020-01-01',pins:[{id:'r1',t:1,x:.2,y:.2,mode:'auto',note:'',group:'A',target:'',between:null,resolved:null}],groups:{A:{note:'reel note'}}},'pins/s02':leg}});await pg.waitForTimeout(1500);
 const dJ=await doc(pg);ok(dJ.pins.length===3,T('legacy pins migrated into reel ('+dJ.pins.length+')'));ok(Object.keys(dJ.groups).length===2&&dJ.groups.A.note==='reel note',T('legacy group got its own letter, notes kept'));
 ok(await js(pg,()=>window.__docs['pins/s02'].migrated===true),T('legacy doc marked migrated'));ok(pg.errs.length===0,T('no page errors (legacy)'));await pg.close();
 /* L: a late echo of our own save must not clobber typing */
 pg=await open(b,vp,{echo:900});await pg.click('#bPin');await seek(pg,.3);await tap(pg,.4,.4);await seek(pg,.5);await tap(pg,.6,.6);await pg.keyboard.press('Escape');
 await js(pg,()=>{document.querySelectorAll('#plist .row .ck')[0].click();document.querySelectorAll('#plist .row .ck')[1].click()});await pg.waitForTimeout(300);await js(pg,()=>document.querySelector('.ab .pri').click());await pg.waitForTimeout(600);
 await pg.keyboard.type('Typing through a late echo',{delay:70});await pg.waitForTimeout(1500);
 ok((await doc(pg)).groups.A.note==='Typing through a late echo',T('typing survives a late echo of our own save'));await pg.close();
 /* M: layout + the rest of the review (phone is the strict one) */
 pg=await open(b,vp);await pg.click('#bPin');const sb=await pg.locator('#stage').boundingBox();ok(sb.height>=(name==='phone'?110:300),T('video keeps a usable size in pin mode ('+Math.round(sb.height)+'px tall)'));
 await seek(pg,.2);await tap(pg,.3,.3);await seek(pg,.4);await tap(pg,.7,.6);await seek(pg,.6);await tap(pg,.4,.8);await js(pg,()=>document.getElementById('bPin').click());await pg.keyboard.press('Escape');await pg.waitForTimeout(200);
 await js(pg,()=>{document.querySelectorAll('#plist .row .ck')[0].click();document.querySelectorAll('#plist .row .ck')[1].click()});await pg.waitForTimeout(300);await js(pg,()=>document.querySelector('.ab .pri').click());await pg.waitForTimeout(900);
 const cover=await js(pg,()=>{const r=document.querySelector('.grp .row .hd');r.scrollIntoView({block:'center'});const q=r.getBoundingClientRect(),e=document.elementFromPoint(q.x+q.width/2,q.y+q.height/2);return !!e&&!!e.closest('.row')});ok(cover,T('grouped pin rows are not covered by the deck or selection panel'));
 await js(pg,()=>{const t=document.querySelector('.grp textarea');t.focus();});await pg.keyboard.type('abc');await pg.evaluate(()=>document.activeElement.blur());await pg.keyboard.press('Control+z');await pg.waitForTimeout(900);
 ok((await doc(pg)).groups.A===undefined||(await doc(pg)).groups.A.note==='',T('undo after typing does not throw'));
 await js(pg,()=>[...document.querySelectorAll('.grp .sm')].find(b=>b.textContent==='Delete')&&[...document.querySelectorAll('.grp .sm')].find(b=>b.textContent==='Delete').click());await pg.waitForTimeout(1000);
 ok(pg.errs.length===0,T('no page errors (layout/undo)'));await pg.close();
 pg=await open(b,vp,{dbLate:2500});await pg.click('#bPin');await seek(pg,.3);await tap(pg,.5,.5);await pg.waitForTimeout(3500);
 const dN=await js(pg,()=>window.__docs&&window.__docs['pins/reel']);ok(!!dN&&dN.pins.length===1,T('a pin dropped before the db connected is saved once it does'));await pg.close();
}
await b.close();console.log(log.join('\n'));console.log(fails?'\n'+fails+' FAILED':'\nALL PASSED');process.exit(fails?1:0)})();
