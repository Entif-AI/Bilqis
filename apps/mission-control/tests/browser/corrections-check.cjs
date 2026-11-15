const { chromium } = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, "../../../..");
const {assetPathForRendererRequest} = require("../../electron/shell/renderer-protocol.cjs");
const server = http.createServer((req,res)=>{
 const prefix = "/apps/mission-control/renderer";
 const asset = req.url.startsWith(prefix + "/") ? assetPathForRendererRequest("bamf-mc://app" + req.url.slice(prefix.length), path.join(root,"apps/mission-control/renderer")) : null;
 const file = asset;
 if(req.url !== "/" && !file) {res.statusCode=404;res.end();return;}
 if(req.url === '/') {res.setHeader('Content-Type','text/html');res.end('<!doctype html><html lang="en"><head><title>Corrections fixture</title><link rel="stylesheet" href="/apps/mission-control/renderer/visual-tokens.css"><link rel="stylesheet" href="/apps/mission-control/renderer/shell.css"><link rel="stylesheet" href="/apps/mission-control/renderer/components.css"><link rel="stylesheet" href="/apps/mission-control/renderer/corrections/corrections.css"></head><body style="display:block;padding:32px"><div id="shell"><p id="view-summary" hidden></p><section id="domain-context-boundary" class="fixture-card" hidden></section><section id="visual-catalog" hidden></section><main id="domain-view" data-test-id="fixture-host"></main><aside id="inspector" data-test-id="fixture-inspector" aria-hidden="true"><h3 id="inspector-title" data-test-id="fixture-inspector-title"></h3><dl id="inspector-summary" data-test-id="fixture-inspector-summary"></dl><details id="inspector-forensics"><summary>Exact identity and details</summary><dl id="inspector-details" data-test-id="fixture-inspector-details"></dl><code id="inspector-deep-link-value"></code><button id="copy-deep-link">Copy deep link</button></details><button id="open-owner" data-test-id="inspector-open-owner">Open in owning view</button><button id="open-evidence" data-test-id="inspector-open-evidence">Open evidence</button></aside></div><style>[data-test-id="fixture-inspector"][aria-hidden="true"]{display:none}</style></body></html>');return;}
 try { res.setHeader('Content-Type',file.endsWith('.css')?'text/css':'text/javascript');res.end(fs.readFileSync(file)); }catch {res.statusCode=404;res.end();}
});
(async()=>{ await new Promise(r=>server.listen(0,'127.0.0.1',r)); const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1100}});await page.goto(`http://127.0.0.1:${server.address().port}/`);
 const {correctionsJourney}=await import(path.join(root,'apps/mission-control/tests/browser/corrections-journey.mjs'));
 const result = await correctionsJourney(page);
 await page.evaluate(()=>window.mount());
 const label='after';
 fs.mkdirSync('output/playwright/1138',{recursive:true}); await page.screenshot({path:`output/playwright/1138/${label}-dark.png`,fullPage:true});
 const variants = [['dark','comfortable',1440],['light','compact',1440],['dark','comfortable',390],['light','compact',320]];
 const axePath = process.env.BILQIS_AXE_MODULE;
 if(axePath) await page.addScriptTag({path: require.resolve(axePath)});
 result.variants=[];
 for(const [theme,density,width] of variants){
   await page.evaluate(([theme,density])=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.density=density;},[theme,density]);
   await page.setViewportSize({width,height:1100});
   await page.screenshot({path:`output/playwright/1138/${label}-${theme}-${density}-${width}.png`,fullPage:true});
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
   if(overflow) throw new Error(`CORRECTIONS_REFLOW:${width}`);
   const violations=axePath ? await page.evaluate(async()=> (await axe.run('[data-test-id="corrections-workspace"]',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(({id,impact,nodes})=>({id,impact,count:nodes.length}))) : null;
   result.variants.push({theme,density,width,overflow,violations});
   if(violations?.length) throw new Error(JSON.stringify(violations));
   await page.locator('[data-test-id="corrections-graph-toggle"]').click();
   const graphViolations=axePath ? await page.evaluate(async()=> (await axe.run('[data-test-id="corrections-workspace"]',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(({id,impact,nodes})=>({id,impact,count:nodes.length}))) : null;
   result.variants[result.variants.length-1].graphViolations=graphViolations;
   if(graphViolations?.length) throw new Error(JSON.stringify(graphViolations));
   if(width===1440 && theme==='dark') await page.screenshot({path:'output/playwright/1138/after-graph-dark-1440.png',fullPage:true});
   await page.locator('[data-test-id="corrections-graph-toggle"]').click();
 }
 await page.evaluate(async()=>{
   const {correctionsT}=await import('/apps/mission-control/renderer/corrections/corrections-messages.mjs');
   const {renderCorrectionsMarkup}=await import('/apps/mission-control/renderer/corrections/corrections-view.mjs');
   document.querySelector('[data-test-id="fixture-host"]').innerHTML=renderCorrectionsMarkup((key,parameters)=>`[Expanded translation] ${correctionsT(key,parameters)}`);
 });
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('CORRECTIONS_TRANSLATION_REFLOW');
 result.translationExpansion=true;
 await page.screenshot({path:'output/playwright/1138/after-expanded-320.png',fullPage:true});
 await page.evaluate(()=>{
   document.documentElement.dir='rtl';
   document.querySelector('[data-test-id="corrections-workspace"]').style.cssText='line-height:1.5;letter-spacing:.12em;word-spacing:.16em';
 });
 await page.emulateMedia({reducedMotion:'reduce'});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('CORRECTIONS_TEXT_SPACING_RTL_REFLOW');
 result.rtlTextSpacingReducedMotion=true;
 await page.screenshot({path:'output/playwright/1138/after-rtl-text-spacing-320.png',fullPage:true});
 fs.writeFileSync('output/playwright/1138/browser-result.json',JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result));
 await browser.close();server.close();console.log(label+' screenshots saved');
})().catch(e=>{console.error(e);server.close();process.exit(1)});
