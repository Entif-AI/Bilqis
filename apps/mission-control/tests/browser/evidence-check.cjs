const { chromium } = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, "../../../..");
const {assetPathForRendererRequest} = require("../../electron/shell/renderer-protocol.cjs");
const server = http.createServer((req,res)=>{
 const prefix = "/apps/mission-control/renderer";
 const asset = req.url.startsWith(prefix + "/") ? assetPathForRendererRequest("bamf-mc://app" + req.url.slice(prefix.length), path.join(root,"apps/mission-control/renderer")) : null;
 const file = asset;
 if(req.url !== "/" && !file) {res.statusCode=404;res.end();return;}
 if(req.url === '/') {res.setHeader('Content-Type','text/html');res.end('<!doctype html><html lang="en"><head><title>Evidence fixture</title><link rel="stylesheet" href="/apps/mission-control/renderer/visual-tokens.css"><link rel="stylesheet" href="/apps/mission-control/renderer/shell.css"><link rel="stylesheet" href="/apps/mission-control/renderer/components.css"><link rel="stylesheet" href="/apps/mission-control/renderer/evidence/evidence.css"></head><body style="display:block;padding:32px"><main data-test-id="fixture-host"></main></body></html>');return;}
 try { res.setHeader('Content-Type',file.endsWith('.css')?'text/css':'text/javascript');res.end(fs.readFileSync(file)); }catch {res.statusCode=404;res.end();}
});
(async()=>{ await new Promise(r=>server.listen(0,'127.0.0.1',r)); const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1100}});await page.goto(`http://127.0.0.1:${server.address().port}/`);
 await page.evaluate(async()=>{
 const {renderEvidenceMarkup}=await import('/apps/mission-control/renderer/evidence/evidence-markup.mjs');
 const record={schema_version:'bilqis.bamf.mission-control.operator-action-receipt/v2',meta:{record_id:'cp05:operation-20261114:completed',authority:'MEASURED',coverage:'COMPLETE',run:{run_id:'bamf-alpha-20261114',generation:44238},materialized_at:1794699300,observed_at:1794699298,as_of:44238,source_refs:['source:curriculum:boolean-composition:v1'],evidence_refs:['evidence:grader:44238:retention'],receipt_refs:['receipt:custody:44238']},operation_id:'operation-20261114',state:'COMPLETED',target_ref:'run:bamf-alpha-20261114',postcondition_ref:'postcondition:checkpoint-and-own-adamw-verified',error_ref:null};
 const related={relation:'supported_by',source_record_id:record.meta.record_id,target_ref:'evidence:grader:44238:retention',target_record_id:null};
 window.fixtureState={status:'ready',criteria:{kind:'record',value:record.meta.record_id},records:[record,{...record,meta:{...record.meta,record_id:'checkpoint:44238:9e37f2a19bb3'},schema_version:'bilqis.bamf.mission-control.checkpoint/v1'},{...record,meta:{...record.meta,record_id:'capability:boolean-and:44238'},schema_version:'bilqis.bamf.mission-control.capability-snapshot/v1'}],links:[related],selected:record,selectedLinks:{state:'PRESENT',coverage:'COMPLETE',links:[related],returned:1,total_matches:1},page:{state:'PRESENT',coverage:'COMPLETE',returned:4,total_matches:4,markers:[],links:[related]},returnAvailable:true,origin:{view:'capability',selected:{kind:'capability',id:'B.AND'},context:{runId:'bamf-alpha-20261114',generation:44238,mode:'LIVE'}}};
 window.paint=(translate)=>document.querySelector('[data-test-id="fixture-host"]').innerHTML=renderEvidenceMarkup(window.fixtureState,translate);window.paint();
 });
 const {evidenceJourney}=await import(path.join(root,'apps/mission-control/tests/browser/evidence-journey.mjs'));
 const result = await evidenceJourney(page);
 await page.evaluate(()=>window.paint());
 const label='after';
 fs.mkdirSync('output/playwright/1141',{recursive:true}); await page.screenshot({path:`output/playwright/1141/${label}-dark.png`,fullPage:true});
 const variants = [['dark','comfortable',1440],['light','compact',1440],['dark','comfortable',390],['light','compact',320]];
 const axePath = process.env.BILQIS_AXE_MODULE;
 if(axePath) await page.addScriptTag({path: require.resolve(axePath)});
 result.variants=[];
 for(const [theme,density,width] of variants){
   await page.evaluate(([theme,density])=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.density=density;},[theme,density]);
   await page.setViewportSize({width,height:1100});
   await page.screenshot({path:`output/playwright/1141/${label}-${theme}-${density}-${width}.png`,fullPage:true});
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
   if(overflow) throw new Error(`EVIDENCE_REFLOW:${width}`);
   const violations=axePath ? await page.evaluate(async()=> (await axe.run('[data-test-id="evidence-workspace"]',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(({id,impact,nodes})=>({id,impact,count:nodes.length}))) : null;
   result.variants.push({theme,density,width,overflow,violations});
   if(violations?.length) throw new Error(JSON.stringify(violations));
 }
 await page.evaluate(async()=>{
   const {evidenceT}=await import('/apps/mission-control/renderer/evidence/evidence-messages.mjs');
   window.paint((key,parameters)=>`[Expanded translation] ${evidenceT(key,parameters)}`);
 });
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('EVIDENCE_TRANSLATION_REFLOW');
 result.translationExpansion=true;
 await page.screenshot({path:'output/playwright/1141/after-expanded-320.png',fullPage:true});
 await page.evaluate(()=>{
   document.documentElement.dir='rtl';
   document.querySelector('[data-test-id="evidence-workspace"]').style.cssText='line-height:1.5;letter-spacing:.12em;word-spacing:.16em';
 });
 await page.emulateMedia({reducedMotion:'reduce'});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('EVIDENCE_TEXT_SPACING_RTL_REFLOW');
 result.rtlTextSpacingReducedMotion=true;
 await page.screenshot({path:'output/playwright/1141/after-rtl-text-spacing-320.png',fullPage:true});
 fs.writeFileSync('output/playwright/1141/browser-result.json',JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result));
 await browser.close();server.close();console.log(label+' screenshots saved');
})().catch(e=>{console.error(e);server.close();process.exit(1)});
