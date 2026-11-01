// Native engine diagnostic on an ephemeral ARM64 macOS runner; no account work.
import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn,spawnSync} from 'node:child_process';
import {createServer} from 'node:http';
const root=path.resolve(process.argv[2]);
const executable=path.join(root,'Wayfern.app/Contents/MacOS/Wayfern');
const require=createRequire(path.join(root,'package.json'));
const {chromium}=require('playwright');
if(process.platform!=='darwin'||process.arch!=='arm64')throw new Error('Native ARM64 macOS required');
const state=await fs.mkdtemp('/tmp/donut-arm-');
const env=Object.fromEntries(Object.entries(process.env).filter(([k])=>!k.startsWith('PI_')&&!/TOKEN|SECRET|PASSWORD|API_KEY|LICENSE_KEY|GITHUB|ACTIONS/.test(k.toUpperCase())&&!/^(DONUT|CLOAK|WAYFERN|HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)/i.test(k)));
Object.assign(env,{HOME:path.join(state,'home'),TMPDIR:path.join(state,'tmp')});
for(const dir of [env.HOME,env.TMPDIR])await fs.mkdir(dir,{recursive:true});
const accept=spawnSync(executable,['--accept-terms-and-conditions'],{cwd:root,env,encoding:'utf8',timeout:30000});
if(accept.status!==0)throw new Error('Official isolated consent failed');
const fixture=createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<title>ARM native fixture</title><label>Demo<input id="demo"></label><button id="save" onclick="document.querySelector(\'#result\').textContent=document.querySelector(\'#demo\').value">Save</button><output id="result"></output>');});
await new Promise(resolve=>fixture.listen(0,'127.0.0.1',resolve));
const report={ok:false,scope:'UNMODIFIED official Wayfern ARM64 baseline only; not an authorized-local fork or full kit',nativePlatform:os.platform(),architecture:os.arch(),vendorCredentialProvided:false,sandboxFlagsAdded:false,checks:{}};
const log=await fs.open(path.join(root,'engine-baseline.log'),'a');let child,browser;
try{
 child=spawn(executable,['--headless=new','--remote-debugging-port=0','--user-data-dir='+path.join(state,'profile'),'--no-first-run','--no-default-browser-check','about:blank'],{cwd:root,env,stdio:['ignore',log.fd,log.fd]});
 let port;
 for(let i=0;i<120;i++){
  if(child.exitCode!==null||child.signalCode)throw new Error('Native engine exited '+child.exitCode+' '+child.signalCode);
  try{port=+(await fs.readFile(path.join(state,'profile/DevToolsActivePort'),'utf8')).split('\n')[0];if(port)break;}catch{}
  await new Promise(resolve=>setTimeout(resolve,250));
 }
 if(!port)throw new Error('No CDP listener');
 browser=await chromium.connectOverCDP('http://127.0.0.1:'+port,{timeout:20000});
 const page=await browser.contexts()[0].newPage();await page.goto('http://127.0.0.1:'+fixture.address().port+'/');
 const cdp=await page.context().newCDPSession(page);
 for(const [name,method,params] of [['version','Browser.getVersion',{}],['evaluate','Runtime.evaluate',{expression:'navigator.platform',returnByValue:true}],['perception','Wayfern.capturePagePerception',{}],['getFingerprint','Wayfern.getFingerprint',{}],['hostIdentity','Wayfern.createIdentity',{operatingSystem:'macos'}],['crossLinuxIdentity','Wayfern.createIdentity',{operatingSystem:'linux'}]]){
  try{
   const value=await cdp.send(method,params);
   if(name==='perception'&&!value.nodes?.length)throw new Error('No perception nodes');
   report.checks[name]={ok:true,keys:Object.keys(value),...(name==='perception'?{nodes:value.nodes.length}:{})};
  }catch(error){report.checks[name]={ok:false,error:String(error.message).slice(0,350)};}
 }
 await page.locator('#demo').fill('arm-native-pass');await page.locator('#save').click();
 report.checks.form={ok:(await page.locator('#result').innerText())==='arm-native-pass'};
 report.navigator=await page.evaluate(()=>({platform:navigator.platform,ua:navigator.userAgent,webdriver:navigator.webdriver}));
 // Fingerprint licensing results are observed baseline data, not a fork PASS.
 report.ok=['version','evaluate','form'].every(name=>report.checks[name]?.ok);
}catch(error){report.error=String(error.message).slice(0,700);}
finally{
 if(browser)await browser.close().catch(()=>{});
 if(child&&child.exitCode===null){child.kill();await new Promise(resolve=>setTimeout(resolve,700));if(child.exitCode===null)child.kill('SIGKILL');}
 fixture.closeAllConnections();await new Promise(resolve=>fixture.close(resolve));await log.close();
 await fs.writeFile(path.join(root,'BASELINE.json'),JSON.stringify(report,null,2));
 await fs.rm(state,{recursive:true,force:true});
 console.log(JSON.stringify(report,null,2));
}
process.exit(report.ok?0:1);
