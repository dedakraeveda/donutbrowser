// Maintainer-only real release smoke. Tokens remain in this helper's memory.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import net from 'node:net';
import fs from 'node:fs';
import path from 'node:path';
const kit = path.resolve(process.argv[2]);
const dependencies = createRequire('D:/projects/pi-auth-browser/package.json');
const { chromium } = dependencies('playwright');
const { Client } = await import(pathToFileURL(dependencies.resolve('@modelcontextprotocol/sdk/client/index.js')));
const { StreamableHTTPClientTransport } = await import(pathToFileURL(dependencies.resolve('@modelcontextprotocol/sdk/client/streamableHttp.js')));
async function freePort(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
const debug=process.argv[3] ? Number(process.argv[3]) : await freePort();
const bounded=(promise,ms=15000)=>Promise.race([promise,new Promise((_,reject)=>setTimeout(()=>reject(new Error('stage-timeout')),ms))]);
const stage=name=>console.log(JSON.stringify({stage:name}));
const fixture=createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Kit fixture</title><label>Demo <input id="demo"></label><button id="save" onclick="document.querySelector(\'#result\').textContent=document.querySelector(\'#demo\').value">Save</button><output id="result"></output>');});
await new Promise(r=>fixture.listen(0,'127.0.0.1',r));
let browser,ui,client,profileId,pid;const result={ok:false,liveManager:false,liveMcp:false,liveBrowser:false};
try {
 stage('launcher');
 const launch=spawnSync(path.join(kit,'Donut Agent Kit.exe'),[process.argv[3]?'status':'launch','--json'],{encoding:'utf8',windowsHide:true,env:{...process.env,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-address=127.0.0.1 --remote-debugging-port=${debug}`}});
 const output=JSON.parse(launch.stdout.trim());if(!output.ok)throw new Error('launcher-rejected');pid=output.result.pid||output.result.runningPids?.[0];
 for(let i=0;i<60;i++){try{browser=await chromium.connectOverCDP(`http://127.0.0.1:${debug}`);break;}catch{await new Promise(r=>setTimeout(r,500));}}
 if(!browser)throw new Error('manager-webview-unavailable');
 ui=browser.contexts().flatMap(c=>c.pages()).find(p=>/^https?:\/\/tauri.localhost\//.test(p.url()));if(!ui)throw new Error('manager-target-missing');
 stage('manager-ui');
 await ui.waitForFunction(()=>!!window.__TAURI_INTERNALS__,null,{timeout:60000,polling:100});
 await ui.waitForFunction(()=>document.body.innerText.length>50,null,{timeout:60000,polling:100});
 result.liveManager=true;result.onboardingWayfernBlocked=await ui.getByText('Downloading your first browser',{exact:false}).count()>0;
 if(result.onboardingWayfernBlocked)throw new Error('obsolete-onboarding-blocked');
 stage('mcp-start');
 const port=await bounded(ui.evaluate(()=>window.__TAURI_INTERNALS__.invoke('start_mcp_server')));
 const token=await ui.evaluate(async()=>{const s=await window.__TAURI_INTERNALS__.invoke('get_app_settings');return s.mcp_token;});
 if(!token)throw new Error('fixture-mcp-token-missing');
 client=new Client({name:'donut-agent-kit-smoke',version:'1.0.0'});
 stage('mcp-connect');
 await client.connect(new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`),{requestInit:{headers:{Authorization:`Bearer ${token}`}}}));
 const tools=(await client.listTools()).tools;result.liveMcp=true;result.tools=tools.length;
 for(const n of ['create_profile','run_profile','kill_profile','list_tabs','get_page_content'])if(!tools.some(t=>t.name===n))throw new Error('required-tool-missing');
 const call=async(name,args)=>{const r=await client.callTool({name,arguments:args});if(r.isError)throw new Error('tool-rejected-'+name);const t=r.content.find(x=>x.type==='text')?.text;try{return JSON.parse(t);}catch{return t;}};
 stage('profile-create');
 const existing=await call('list_profiles',{});
 const matched=existing.filter(p=>p.name==='Agent Kit disposable fixture'&&p.browser==='cloak');
 if(matched.length>1)throw new Error('ambiguous-fixture-profile');
 if(matched.length)profileId=matched[0].id;
 else {const made=await call('create_profile',{name:'Agent Kit disposable fixture',browser:'cloak'});profileId=made.id||made.profile?.id||String(made).match(/id: ([0-9a-f-]{36})/)?.[1];}
 if(!profileId)throw new Error('fixture-profile-id-missing');
 stage('profile-run');
 const launched=await call('run_profile',{profile_id:profileId,headless:true,url:`http://127.0.0.1:${fixture.address().port}/`});
 const listed=await call('list_tabs',{profile_id:profileId});
 const tabs=Array.isArray(listed)?listed:listed.tabs;
 if(!tabs?.length)throw new Error('native-tabs-missing');
 const chosen=tabs.find(t=>t.url===`http://127.0.0.1:${fixture.address().port}/`)||(tabs.length===1?tabs[0]:null);
 const pageId=chosen?.id||chosen?.page_id;if(!pageId)throw new Error('browser-fixture-target-missing');
 const target={profile_id:profileId,page_id:pageId};
 await call('navigate',{...target,url:`http://127.0.0.1:${fixture.address().port}/`});
 await call('type_text',{...target,selector:'#demo',text:'portable-kit-pass',instant:true});
 await call('click_element',{...target,selector:'#save'});
 const text=await call('get_page_content',{...target,format:'text',selector:'#result'});
 if(!JSON.stringify(text).includes('portable-kit-pass'))throw new Error('form-postcondition-failed');
 result.liveBrowser=true;result.formPostcondition=true;result.nativeTabsListed=true;
 result.webdriver=await call('evaluate_javascript',{...target,expression:'navigator.webdriver'});
 result.ok=true;
} catch(e){result.error=String(e.message||'smoke-failed').replace(/[A-Za-z0-9_-]{40,}/g,'[redacted]').slice(0,160);}
finally {
 if(client&&profileId){for(const name of ['kill_profile','delete_profile'])try{await client.callTool({name,arguments:{profile_id:profileId}});}catch{}}
 if(client)await bounded(client.close(),3000).catch(()=>{});
 if(ui)await bounded(ui.evaluate(()=>window.__TAURI_INTERNALS__.invoke('confirm_quit')),3000).catch(()=>{});
 if(browser)await bounded(browser.close(),3000).catch(()=>{});
 fixture.closeAllConnections();
 await bounded(new Promise(r=>fixture.close(r)),3000).catch(()=>{});
 fs.writeFileSync(path.join(path.dirname(kit),'release-smoke.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
}
process.exit(result.ok?0:1);
