'use strict';
const DEFAULTS = {delivery: 30, quality: 25, cost: 20, geography: 15, concentration: 10};
const LABELS = {delivery: 'Late delivery', quality: 'Quality defects', cost: 'Cost variance', geography: 'Geographic exposure', concentration: 'Spend concentration'};
const TITLES = {
  overview: ['Procurement overview', 'Understand your supplier base and prioritize action.'],
  suppliers: ['Supplier analysis', 'Explore supplier performance and the drivers behind each score.'],
  spend: ['Spend & cost', 'Identify concentration and compare actual versus contracted spend.'],
  methodology: ['Methodology', 'Understand the data, calculations, and limitations.']
};
let state = {data: null, supplierId: null, initialized: false, weights: {...DEFAULTS}, sequence: 0};
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = (value, decimals = 1) => `${(value * 100).toFixed(decimals)}%`;
const money = value => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', notation:'compact', maximumFractionDigits:2}).format(value);
const number = value => new Intl.NumberFormat('en-US').format(value);
const empty = '<div class="empty">No suppliers match the selected filters.</div>';

function setView(view) {
  document.querySelectorAll('.view').forEach(el => { el.hidden = el.id !== `view-${view}`; });
  document.querySelectorAll('.nav-link').forEach(el => { el.classList.toggle('active', el.dataset.view === view); });
  $('page-title').textContent = TITLES[view][0];
  $('page-subtitle').textContent = TITLES[view][1];
  window.scrollTo({top: 0, behavior: 'smooth'});
}
function query() {
  const params = new URLSearchParams({category:$('category-filter').value, region:$('region-filter').value});
  Object.entries(state.weights).forEach(([key, value]) => params.set(key, String(value)));
  return params.toString();
}
function populateSelect(id, values) {
  const select = $(id), value = select.value;
  select.innerHTML = ['All', ...values].map(x => `<option value="${esc(x)}">${esc(x)}</option>`).join('');
  select.value = value || 'All';
}
function drawBars(container, rows, value, maximum, format, useBand = false) {
  if (!rows.length) { container.innerHTML = empty; return; }
  container.innerHTML = rows.map(row => {
    const width = Math.max(0, Math.min(100, maximum ? value(row) / maximum * 100 : 0));
    const cls = useBand ? row.risk_band.toLowerCase() : '';
    return `<div class="bar-row"><span class="bar-name" title="${esc(row.name)}">${esc(row.name)}</span><div class="bar-track"><div class="bar-fill ${cls}" style="width:${width}%"></div></div><span class="bar-value">${esc(format(value(row)))}</span></div>`;
  }).join('');
}
function categoryTotals(rows) {
  const totals = {};
  rows.forEach(r => { totals[r.category] = (totals[r.category] || 0) + r.actual_spend; });
  return Object.entries(totals).map(([name, value]) => ({name, value})).sort((a,b) => b.value-a.value);
}
function renderOverview(data) {
  const s=data.summary, rows=data.suppliers;
  $('metric-spend').textContent = money(s.total_spend);
  $('metric-orders').textContent = number(s.po_count);
  $('metric-suppliers').textContent = `${s.supplier_count} suppliers in selection`;
  $('metric-late').textContent = pct(s.late_rate);
  $('metric-defects').textContent = pct(s.defect_rate, 2);
  $('metric-high').textContent = s.high_risk_count;
  drawBars($('top-risk'), rows.slice(0,8).map(r => ({name:r.supplier_name, risk_band:r.risk_band, value:r.risk_score})), r=>r.value, 100, x=>x.toFixed(1), true);
  const counts = ['High','Medium','Low'].map(band => ({band, count:rows.filter(r=>r.risk_band===band).length}));
  $('risk-mix').innerHTML = rows.length ? counts.map(({band,count})=>`<div class="risk-row"><span><span class="pill ${band.toLowerCase()}">${band}</span></span><div class="bar-track"><div class="bar-fill ${band.toLowerCase()}" style="width:${100*count/rows.length}%"></div></div><b>${count}</b></div>`).join('') : empty;
  $('insight-text').textContent = rows.length ? `${rows[0].supplier_name} has the highest modeled risk (${rows[0].risk_score.toFixed(1)} / 100). Review its drivers before making a sourcing decision.` : 'Change the filters to see supplier insights.';
  const categories=categoryTotals(rows);
  $('category-spend').innerHTML = categories.length ? categories.map(c=>`<div class="category-tile"><span>${esc(c.name)}</span><strong>${money(c.value)}</strong></div>`).join('') : empty;
}
function renderDetail() {
  const row=state.data.suppliers.find(r=>r.supplier_id===state.supplierId);
  $('ai-button').disabled=!row;
  if (!row) { $('supplier-detail').innerHTML=empty; return; }
  const drivers=Object.entries(row.contributions).sort((a,b)=>b[1]-a[1]);
  const driverHTML=drivers.map(([key,val])=>`<div class="driver-row"><span>${esc(LABELS[key])}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100,val)}%"></div></div><b>${val.toFixed(1)}</b></div>`).join('');
  const recHTML=row.recommendations.map(r=>`<div class="recommendation"><strong>${esc(r.driver)}</strong><p>${esc(r.evidence)} ${esc(r.action)}</p></div>`).join('');
  const factTiles=[
    ['Late orders',pct(row.late_rate),`${number(row.late_orders)} of ${number(row.po_count)} POs`],
    ['Defective units',pct(row.defect_rate,2),`${number(row.defect_units)} of ${number(row.units)} units`],
    ['Cost variance',`${row.cost_variance_rate>=0?'+':''}${pct(row.cost_variance_rate)}`,'vs. contracted'],
    ['Geo. exposure',`${row.geo_exposure.toFixed(0)} / 100`,'scenario input'],
    ['Category share',pct(row.category_share),'of category spend']
  ];
  const facts=factTiles.map(([label,value,note])=>`<div><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`).join('');
  $('supplier-detail').innerHTML=`<div class="detail-heading"><strong>${row.risk_score.toFixed(1)}</strong><span>/ 100</span><span class="pill ${row.risk_band.toLowerCase()}">${esc(row.risk_band)} risk</span></div><div class="detail-stats">${facts}</div>${driverHTML}<div class="recommendation"><strong>Rule-based next steps</strong><p>Based on the two largest weighted risk contributions.</p></div>${recHTML}`;
}
function renderSuppliers(data) {
  const rows=data.suppliers;
  $('supplier-table').innerHTML=rows.length ? rows.map(r=>`<tr tabindex="0" data-id="${esc(r.supplier_id)}" aria-label="Inspect ${esc(r.supplier_name)}"><td>${esc(r.supplier_name)}</td><td>${esc(r.category)}</td><td>${r.po_count}</td><td>${money(r.actual_spend)}</td><td>${pct(r.late_rate)}</td><td>${pct(r.defect_rate,2)}</td><td><span class="pill ${r.risk_band.toLowerCase()}">${r.risk_score.toFixed(1)} · ${esc(r.risk_band)}</span></td></tr>`).join('') : '<tr><td colspan="7">No suppliers match the selected filters.</td></tr>';
  if (!rows.some(r=>r.supplier_id===state.supplierId)) state.supplierId=rows[0]?.supplier_id || null;
  $('supplier-select').innerHTML=rows.length ? rows.map(r=>`<option value="${esc(r.supplier_id)}">${esc(r.supplier_name)}</option>`).join('') : '<option value="">No suppliers</option>';
  $('supplier-select').value=state.supplierId || '';
  renderDetail();
}
function renderSpend(data) {
  const s=data.summary, rows=data.suppliers;
  $('spend-actual').textContent=money(s.total_spend); $('spend-contract').textContent=money(s.contracted_spend);
  $('spend-variance').textContent=`${s.cost_variance_rate>=0?'+':''}${pct(s.cost_variance_rate)}`;
  const cats=categoryTotals(rows);
  drawBars($('spend-bars'),cats,r=>r.value,cats[0]?.value || 0,money);
  const top=[...rows].sort((a,b)=>b.actual_spend-a.actual_spend).slice(0,7).map(r=>({name:r.supplier_name,value:r.actual_spend}));
  drawBars($('spend-suppliers'),top,r=>r.value,top[0]?.value || 0,money);
}
function renderWeights() {
  $('weights').innerHTML=Object.entries(state.weights).map(([key,value])=>`<div class="weight-row"><div class="weight-label"><label for="weight-${key}">${esc(LABELS[key])}</label><b id="weight-value-${key}">${value}</b></div><input id="weight-${key}" type="range" min="0" max="100" step="5" value="${value}" data-weight="${key}"></div>`).join('');
  document.querySelectorAll('[data-weight]').forEach(input=>input.addEventListener('input',()=>{
    state.weights[input.dataset.weight]=Number(input.value);
    $(`weight-value-${input.dataset.weight}`).textContent=input.value;
    clearTimeout(state.timer); state.timer=setTimeout(updateReport,160);
  }));
}
async function updateReport() {
  if (Object.values(state.weights).every(x=>x===0)) { $('error').textContent='At least one risk weight must be above zero.'; $('error').hidden=false; return; }
  const sequence=++state.sequence;
  try {
    const response=await fetch(`/api/report?${query()}`);
    const data=await response.json();
    if (!response.ok) throw new Error(data.error || 'Unable to load dashboard.');
    if (sequence!==state.sequence) return;
    $('error').hidden=true; state.data=data;
    if (!state.initialized) { populateSelect('category-filter',data.categories); populateSelect('region-filter',data.regions); state.initialized=true; }
    $('export-link').href=`/api/export.csv?${query()}`;
    renderOverview(data); renderSuppliers(data); renderSpend(data);
    $('ai-output').textContent='Select a supplier and generate a brief. The score and rule-based recommendations above work without AI.';
  } catch (err) { if(sequence===state.sequence){$('error').textContent=err.message; $('error').hidden=false;} }
}
document.querySelectorAll('.nav-link').forEach(btn=>btn.addEventListener('click',()=>setView(btn.dataset.view)));
document.querySelectorAll('.goto-suppliers').forEach(btn=>btn.addEventListener('click',()=>setView('suppliers')));
document.querySelectorAll('.goto-spend').forEach(btn=>btn.addEventListener('click',()=>setView('spend')));
['category-filter','region-filter'].forEach(id=>$(id).addEventListener('change',updateReport));
$('reset-filters').addEventListener('click',()=>{$('category-filter').value='All';$('region-filter').value='All';updateReport();});
$('reset-weights').addEventListener('click',()=>{state.weights={...DEFAULTS};renderWeights();updateReport();});
$('supplier-select').addEventListener('change',e=>{state.supplierId=e.target.value;renderDetail();$('ai-output').textContent='Select Generate AI brief to analyze this supplier.';});
function selectRow(target){ const row=target.closest('tr[data-id]'); if(!row)return; state.supplierId=row.dataset.id;$('supplier-select').value=state.supplierId;renderDetail();$('ai-output').textContent='Select Generate AI brief to analyze this supplier.';$('supplier-detail').scrollIntoView({behavior:'smooth',block:'center'}); }
$('supplier-table').addEventListener('click',e=>selectRow(e.target));
$('supplier-table').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRow(e.target);}});
$('ai-button').addEventListener('click',async()=>{
  if(!state.supplierId)return;
  const button=$('ai-button'), supplierId=state.supplierId, sequence=state.sequence;
  button.disabled=true;$('ai-output').textContent='Generating an AI brief…';
  try { const response=await fetch('/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({supplier_id:supplierId,weights:state.weights})});const result=await response.json();if(!response.ok)throw new Error(result.error||'Unable to generate brief.');if(state.supplierId===supplierId && state.sequence===sequence) $('ai-output').textContent=result.text; }
  catch(err){if(state.supplierId===supplierId && state.sequence===sequence) $('ai-output').textContent=err.message;}
  finally{button.disabled=!state.supplierId;}
});
renderWeights();updateReport();
