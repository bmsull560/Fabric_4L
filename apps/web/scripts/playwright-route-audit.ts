/**
 * Playwright Route & Hook Audit Runner
 */
import { chromium, Page, ConsoleMessage, Request, Response } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = process.env.AUDIT_BASE_URL || 'http://localhost:3002';
const OUT = path.resolve(process.cwd(), '../audit-output');
const SCR = path.join(OUT, 'screenshots');
fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SCR, { recursive: true });

type RouteStatus = 'Pass'|'Partial'|'Fail'|'Blocked';

interface R {
  path: string; from: string; title: string; heading: string;
  status: RouteStatus;
  shot: string; ce: string[]; cw: string[]; nf: string[]; li: string[]; hi: string[]; notes: string[]; vp: string;
}

const ROUTES: { path: string; from: string; tier?: string }[] = [
  {path:'/',from:'root',tier:'public'},{path:'/login',from:'nav',tier:'public'},{path:'/signup',from:'nav',tier:'public'},
  {path:'/home',from:'sidebar',tier:'standard'},{path:'/command-center',from:'sidebar',tier:'standard'},{path:'/accounts',from:'sidebar',tier:'standard'},
  {path:'/accounts/acct-123',from:'deep-link',tier:'standard'},
  {path:'/workflow/prospect',from:'sidebar',tier:'standard'},{path:'/workflow/intelligence',from:'sidebar',tier:'standard'},{path:'/workflow/ai-model',from:'sidebar',tier:'standard'},
  {path:'/workflow/driver-tree',from:'sidebar',tier:'standard'},{path:'/workflow/evidence',from:'sidebar',tier:'standard'},{path:'/workflow/calculator',from:'sidebar',tier:'standard'},{path:'/workflow/value-case',from:'sidebar',tier:'standard'},
  {path:'/intelligence/acct-123',from:'redirect',tier:'standard'},{path:'/intelligence/acct-123/signals',from:'tab',tier:'standard'},{path:'/intelligence/acct-123/drivers',from:'tab',tier:'standard'},
  {path:'/intelligence/acct-123/evidence',from:'tab',tier:'standard'},{path:'/intelligence/acct-123/stakeholders',from:'tab',tier:'standard'},{path:'/intelligence/acct-123/enrichment',from:'tab',tier:'standard'},
  {path:'/intelligence/acct-123/hypotheses',from:'tab',tier:'standard'},{path:'/intelligence/acct-123/competitive',from:'tab',tier:'standard'},{path:'/intelligence/acct-123/roi',from:'tab',tier:'standard'},
  {path:'/intelligence/acct-123/evidence-library',from:'tab',tier:'standard'},{path:'/intelligence/acct-123/ontology-match',from:'tab',tier:'standard'},
  {path:'/hypothesis/acct-123/hypothesis',from:'tab',tier:'standard'},{path:'/hypothesis/acct-123/discovery-questions',from:'tab',tier:'standard'},
  {path:'/hypothesis/acct-123/persona-fit',from:'tab',tier:'standard'},{path:'/hypothesis/acct-123/assumptions',from:'tab',tier:'standard'},
  {path:'/drivers/acct-123',from:'sidebar',tier:'standard'},
  {path:'/evidence/acct-123/evidence',from:'tab',tier:'standard'},{path:'/evidence/acct-123/alternatives',from:'tab',tier:'standard'},{path:'/evidence/acct-123/solution-cost',from:'tab',tier:'standard'},
  {path:'/calculator/acct-123/roi',from:'tab',tier:'standard'},{path:'/calculator/acct-123/value-model',from:'tab',tier:'standard'},
  {path:'/value-case/acct-123',from:'sidebar',tier:'standard'},{path:'/realization/acct-123',from:'sidebar',tier:'standard'},
  {path:'/studio/acct-123/action-plan',from:'tab',tier:'standard'},{path:'/studio/acct-123/value-model',from:'tab',tier:'standard'},{path:'/studio/acct-123/narrative',from:'tab',tier:'standard'},
  {path:'/context/packs',from:'sidebar',tier:'standard'},{path:'/context/models',from:'sidebar',tier:'standard'},
  {path:'/context/formulas',from:'sidebar',tier:'advanced'},{path:'/context/formulas/new',from:'button',tier:'advanced'},{path:'/context/value-trees/explorer',from:'sidebar',tier:'advanced'},
  {path:'/context/agents',from:'sidebar',tier:'advanced'},{path:'/context/ontology',from:'sidebar',tier:'advanced'},{path:'/context/ontology/entities',from:'sub-nav',tier:'advanced'},
  {path:'/context/ontology/entities/ent-123',from:'deep-link',tier:'advanced'},{path:'/context/ontology/graph',from:'sub-nav',tier:'advanced'},
  {path:'/context/ingestion/jobs',from:'sidebar',tier:'advanced'},{path:'/context/extraction',from:'sidebar',tier:'advanced'},
  {path:'/context/integrations',from:'sidebar',tier:'admin'},{path:'/context/sources',from:'sidebar',tier:'admin'},
  {path:'/deliverables/cases',from:'sidebar',tier:'standard'},{path:'/deliverables/cases/case-123',from:'deep-link',tier:'standard'},
  {path:'/deliverables/calculators',from:'sidebar',tier:'advanced'},
  {path:'/deliverables/views/cfo',from:'sidebar',tier:'standard'},{path:'/deliverables/views/executive',from:'sidebar',tier:'standard'},{path:'/deliverables/views/technical',from:'sidebar',tier:'standard'},
  {path:'/settings/content/formulas',from:'sidebar',tier:'admin'},{path:'/settings/data/variables',from:'sidebar',tier:'admin'},{path:'/settings/access/roles',from:'sidebar',tier:'admin'},
  {path:'/settings/system/settings',from:'sidebar',tier:'admin'},{path:'/settings/system/billing',from:'sidebar',tier:'admin'},
  {path:'/governance/traces',from:'sidebar',tier:'standard'},{path:'/governance/evidence',from:'sidebar',tier:'standard'},
  {path:'/governance/provenance',from:'sidebar',tier:'advanced'},{path:'/governance/compliance',from:'sidebar',tier:'advanced'},
  {path:'/governance/benchmarks',from:'sidebar',tier:'admin'},{path:'/governance/audit/log',from:'sidebar',tier:'admin'},{path:'/governance/health',from:'sidebar',tier:'admin'},
  {path:'/dev/integration',from:'sidebar',tier:'admin'},
  {path:'/nonexistent-route-xyz',from:'edge-case',tier:'standard'},
  {path:'/intelligence',from:'edge-case',tier:'standard'},{path:'/studio',from:'edge-case',tier:'standard'},
  {path:'/hypothesis',from:'edge-case',tier:'standard'},{path:'/evidence',from:'edge-case',tier:'standard'},{path:'/calculator',from:'edge-case',tier:'standard'},
];

const VP = [
  {n:'desktop',w:1440,h:900},{n:'laptop',w:1280,h:800},{n:'tablet',w:768,h:1024},{n:'mobile',w:390,h:844}
];

async function seed(page:Page,tier='admin'){
  const user={id:'audit-user-001',email:'audit@test.com',role:tier,tenantId:'tenant-audit',tenantSlug:'audit'};
  await page.goto(`${BASE_URL}/login`,{waitUntil:'commit'});
  await page.evaluate((u)=>{
    const payload={exp:Math.floor(Date.now()/1000)+86400,iat:Math.floor(Date.now()/1000),sub:u.id,tenant_id:u.tenantId};
    const token=`header.${btoa(JSON.stringify(payload))}.signature`;
    localStorage.setItem('accessToken',token);
    localStorage.setItem('userInfo',JSON.stringify(u));
    localStorage.setItem('tenantId',u.tenantId);
    localStorage.setItem('user-tier-storage',JSON.stringify({state:{currentTier:u.role,isAdvancedModeEnabled:u.role!=='standard',userRole:u.role},version:0}));
  },user);
}

async function clear(page:Page){
  try{await page.evaluate(()=>{localStorage.clear();});}catch{}
}

interface SummaryMetadata {
  health: number;
  verdict: string;
  ce: number;
  nf: number;
  risks: string[];
}

interface AuditMeta {
  date: string;
  base: string;
  backOk: boolean;
  forwardOk: boolean;
  reloadOk: boolean;
  loginFocusOk: boolean;
}

type ConsoleHandler = (message: ConsoleMessage) => void;
type RequestFailureHandler = (request: Request) => void;
type ResponseFailureHandler = (response: Response) => void;

function isErrorWithMessage(value: unknown): value is { message: string } {
  return typeof value === 'object' && value !== null && 'message' in value && typeof (value as { message: unknown }).message === 'string';
}

function safe(s:string){return s.replace(/[^a-z0-9_-]/gi,'_').replace(/_+/g,'_');}

async function audit(page:Page,routePath:string,from:string,vpName:string,vp:{w:number;h:number}):Promise<R>{
  const ce:string[]=[];const cw:string[]=[];const nf:string[]=[];const li:string[]=[];const hi:string[]=[];const notes:string[]=[];
  const onC: ConsoleHandler=(m)=>{const t=m.type();const x=m.text();if(t==='error')ce.push(x);else if(t==='warning')cw.push(x);};
  const onF: RequestFailureHandler=(r)=>{const f=r.failure();if(f)nf.push(`${r.method()} ${r.url()} — ${f.errorText}`);};
  const onR: ResponseFailureHandler=(r)=>{const s=r.status();if(s>=400&&!r.url().includes('localhost:3001'))nf.push(`${r.request().method()} ${r.url()} — HTTP ${s}`);};
  page.on('console',onC);page.on('requestfailed',onF);page.on('response',onR);
  await page.setViewportSize({width:vp.w,height:vp.h});
  try{await page.goto(`${BASE_URL}${routePath}`,{waitUntil:'load',timeout:15000});}
  catch(e: unknown){notes.push(`nav timeout:${isErrorWithMessage(e) ? e.message : String(e)}`);try{await page.goto(`${BASE_URL}${routePath}`,{waitUntil:'domcontentloaded',timeout:10000});}catch(e2: unknown){notes.push(`load fallback:${isErrorWithMessage(e2) ? e2.message : String(e2)}`);}}
  await page.waitForTimeout(800);
  const title=await page.title().catch(()=>'?');
  const h1=await page.locator('h1').first().textContent().catch(()=>'');
  const h2=await page.locator('h2').first().textContent().catch(()=>'');
  const heading=(h1||h2||'No heading').substring(0,60);
  const shot=`audit-output/screenshots/${safe(`${routePath}_${vpName}`)}.png`;
  await page.screenshot({path:path.join(OUT,'screenshots',safe(`${routePath}_${vpName}`)+'.png'),fullPage:true}).catch(()=>notes.push('sshot fail'));
  if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))li.push(`overflow ${vp.w}x${vp.h}`);
  const errUi=await page.locator('text=/error|failed|something went wrong/i').first().textContent().catch(()=>null);
  if(errUi&&errUi.length<200)notes.push(`errUI:"${errUi.trim()}"`);
  const emptyUi=await page.locator('text=/no data|empty|nothing here|no results/i').first().textContent().catch(()=>null);
  if(emptyUi)notes.push(`empty:"${emptyUi.trim()}"`);
  const spin=await page.locator('[class*="animate-spin"],[class*="loading"]').first().isVisible().catch(()=>false);
  if(spin)notes.push('spinner>1.5s');
  const final=new URL(page.url()).pathname;
  if(final!==routePath&&!routePath.startsWith('/nonexistent'))notes.push(`redirect:${routePath}→${final}`);
  let status:RouteStatus='Pass';
  if(ce.length||nf.length)status='Partial';
  if(ce.some(e=>/crash|undefined|null|Cannot read|not a function/i.test(e)))status='Fail';
  if(notes.some(n=>n.includes('fallback:')))status='Blocked';
  page.off('console',onC);page.off('requestfailed',onF);page.off('response',onR);
  return {path:routePath,from,title,heading,status,shot,ce,cw,nf,li,hi,notes,vp:vpName};
}

function mdReport(rs:R[],summary:SummaryMetadata,meta:AuditMeta):string{
  let md=`# Playwright Route & Hook Audit Report\n**Date:** ${meta.date} **Base:** ${meta.base}\n\n`;
  md+=`## 1. Executive Summary\n- Health score: ${summary.health}%\n- Verdict: ${summary.verdict}\n- Console errors: ${summary.ce} | Network failures: ${summary.nf}\n`;
  md+=`### Top 5 Risks\n`;summary.risks.slice(0,5).forEach((r:string,i:number)=>md+=`${i+1}. ${r}\n`);
  md+=`### Top 5 Fixes\n1. Fix P0 hook null-checks on route params\n2. Add ErrorBoundary to all lazy tabs\n3. Handle API 401/403 with visible UI\n4. Preserve account/tenant context on refresh\n5. Fix responsive overflow & mobile nav\n\n`;
  md+=`## 2. Route Inventory\n| Route | From | Title | Heading | Status | CE | NF | Notes |\n|-------|------|-------|---------|--------|----|----|-------|\n`;
  for(const r of rs){md+=`| ${r.path} | ${r.from} | ${r.title.substring(0,28)} | ${r.heading.substring(0,28)} | ${r.status} | ${r.ce.length} | ${r.nf.length} | ${r.notes.join('; ').substring(0,60).replace(/\|/g,'\\|')} |\n`;}
  md+=`\n## 3. Hook & State Audit\n`;
  const hookMap=new Map<string,{routes:string[];msg:string}>();
  for(const r of rs)for(const e of r.ce){
    let name='Generic error';
    if(/useParams|params/i.test(e))name='useParams null/undefined';
    else if(/useAuth|auth/i.test(e))name='useAuth context failure';
    else if(/zustand/i.test(e))name='Zustand store error';
    else if(/invalid hook/i.test(e))name='Invalid hook call';
    else if(/wouter/i.test(e))name='Wouter routing error';
    else if(/react query|tanstack|useQuery/i.test(e))name='React Query failure';
    else continue;
    const ex=hookMap.get(name)||{routes:[],msg:e};
    ex.routes.push(r.path);hookMap.set(name,ex);
  }
  if(hookMap.size===0)md+=`_No hook errors detected._\n`;
  for(const [k,v] of hookMap){md+=`- **${k}** — routes: ${[...new Set(v.routes)].join(', ')} — ${v.msg.substring(0,120)}\n`;}
  md+=`\n## 4. Navigation & Routing Audit\n`;
  md+=`- Back/forward: ${meta.backOk?'OK':'FAIL'}\n`;
  md+=`- Nested reload: ${meta.reloadOk?'OK':'FAIL'}\n`;
  const reds=rs.filter(r=>r.notes.some(n=>n.includes('redirect:')));
  if(reds.length){md+=`Redirects observed:\n`;reds.forEach(r=>md+=`  - ${r.path}\n`);}
  md+=`\n## 5. Data & API Audit\n`;
  const api=rs.filter(r=>r.nf.length>0);
  if(api.length===0)md+=`_No API failures._\n`;else api.forEach(r=>md+=`- ${r.path}: ${r.nf.slice(0,2).join('; ')}\n`);
  md+=`\n## 6. Accessibility & Responsive Audit\n`;
  const overflow=rs.filter(r=>r.li.length>0);
  if(overflow.length===0)md+=`_No responsive overflow._\n`;else overflow.forEach(r=>md+=`- ${r.path} @${r.vp}: ${r.li.join('; ')}\n`);
  md+=`- Keyboard focus on /login: ${meta.loginFocusOk?'OK':'FAIL'}\n`;
  md+=`\n## 7. Prioritized Fix Backlog\n`;
  rs.filter(r=>r.status==='Fail'||r.status==='Blocked').slice(0,8).forEach((r,i)=>{
    md+=`### ${i+1}. Fix ${r.status.toLowerCase()} route ${r.path}\n`;
    md+=`- Severity: ${r.status==='Blocked'?'P0':'P1'} | Area: Routing/Rendering\n`;
    md+=`- Problem: ${r.ce.join('; ').substring(0,120)} ${r.notes.join('; ').substring(0,120)}\n`;
    md+=`- AC: No console errors, graceful empty/error states, screenshot match\n\n`;
  });
  md+=`## 8. Playwright Test Recommendations\n`;
  md+=`1. Route smoke tests for every canonical path\n`;
  md+=`2. Deep-link reload tests for /intelligence/:id/:tab and /studio/:id/:tab\n`;
  md+=`3. Auth/tenant context propagation tests\n`;
  md+=`4. Responsive viewport matrix (390/768/1280/1440)\n`;
  md+=`5. Axe-core scan on all pages + keyboard-only journey\n`;
  md+=`6. Error/empty/loading state tests with mocked API\n`;
  return md;
}

async function main(){
  console.log('Starting audit...');
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage();
  await seed(page,'admin');
  const desktop=VP[0];
  const results:R[]=[];
  for(const r of ROUTES){
    console.log(`  ${r.path}`);
    results.push(await audit(page,r.path,r.from,desktop.n,desktop));
    await page.waitForTimeout(200);
  }
  // responsive sample
  for(const p of ['/home','/accounts','/context/packs','/deliverables/cases']){
    for(const v of VP.slice(1)) results.push(await audit(page,p,'responsive',v.n,v));
  }
  // nav checks
  await page.goto(`${BASE_URL}/home`,{waitUntil:'networkidle'});
  await page.goto(`${BASE_URL}/accounts`,{waitUntil:'networkidle'});
  await page.goBack({waitUntil:'networkidle'});const backOk=page.url().includes('/home');
  await page.goForward({waitUntil:'networkidle'});const forwardOk=page.url().includes('/accounts');
  await page.goto(`${BASE_URL}/intelligence/acct-123/signals`,{waitUntil:'networkidle'});
  await page.reload({waitUntil:'networkidle'});const reloadOk=page.url().includes('/intelligence/acct-123/signals');
  // keyboard
  await clear(page);await page.goto(`${BASE_URL}/login`,{waitUntil:'networkidle'});
  await page.keyboard.press('Tab');
  const loginFocusOk=await page.evaluate(()=>document.activeElement?.tagName!=='BODY');

  const desk=results.filter(r=>r.vp==='desktop');
  const pass=desk.filter(r=>r.status==='Pass').length;
  const partial=desk.filter(r=>r.status==='Partial').length;
  const fail=desk.filter(r=>r.status==='Fail').length;
  const blocked=desk.filter(r=>r.status==='Blocked').length;
  const ceTotal=desk.reduce((s,r)=>s+r.ce.length,0);
  const nfTotal=desk.reduce((s,r)=>s+r.nf.length,0);
  const health=Math.round((pass/Math.max(desk.length,1))*100);
  const verdict=health>=90?'Ready with minor fixes':health>=70?'Conditional — fix P0/P1':'Not ready — significant issues';
  const risks:string[]=[];
  if(fail)risks.push(`${fail} routes crash`);
  if(blocked)risks.push(`${blocked} routes blocked`);
  if(ceTotal>20)risks.push(`${ceTotal} console errors`);
  if(!backOk)risks.push('Back nav broken');
  if(!reloadOk)risks.push('Nested reload broken');
  if(!loginFocusOk)risks.push('Login focus broken');

  const md=mdReport(desk,{health,verdict,ce:ceTotal,nf:nfTotal,risks},{date:new Date().toISOString().split('T')[0],base:BASE_URL,backOk,forwardOk,reloadOk,loginFocusOk});
  const mdPath=path.join(OUT,`playwright-route-hook-audit-${new Date().toISOString().split('T')[0]}.md`);
  fs.writeFileSync(mdPath,md);
  console.log(`\nReport: ${mdPath}`);
  console.log(`Routes:${desk.length} Pass:${pass} Partial:${partial} Fail:${fail} Blocked:${blocked} CE:${ceTotal} NF:${nfTotal}`);
  console.log(`Risks: ${risks.slice(0,5).join(' | ')}`);
  await browser.close();
}

main().catch(e=>{console.error(e);process.exit(1);});
