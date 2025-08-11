// ===== Tabs =====
const tabs = document.querySelectorAll('.tab');
const panes = {
  map: document.getElementById('pane-map'),
  franchise: document.getElementById('pane-franchise'),
  trend: document.getElementById('pane-trend'),
  report: document.getElementById('pane-report'),
};
tabs.forEach(tab=>{
  tab.addEventListener('click',()=>{
    tabs.forEach(t=>t.classList.remove('active'));
    tab.classList.add('active');
    Object.values(panes).forEach(p=>p.hidden=true);
    panes[tab.dataset.tab].hidden=false;
  });
});

// ===== Login dialog (JWT 연동 자리) =====
const dlg = document.getElementById('dlgLogin');
['btnOpenLogin','btnOpenLogin2','btnOpenLogin3'].forEach(id=>{
  const el = document.getElementById(id);
  if(el) el.onclick = ()=>dlg.showModal();
});
document.getElementById('btnLogin')?.addEventListener('click', async (e)=>{
  e.preventDefault();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value.trim();
  // 실제 연동: POST /api/token/
  // const res = await fetch('/api/token/', {...})
  document.getElementById('loginStatus').textContent = '✅ (데모) 로그인 성공';
  setTimeout(()=>dlg.close(), 600);
});

// ===== Demo dots on the grid map (산점도 느낌) =====
(function drawDemoDots(){
  const el = document.getElementById('gridMap');
  if(!el) return;
  const w = el.clientWidth, h = el.clientHeight;
  const points = [
    {x:.18, y:.25, c:'g'}, {x:.32, y:.42, c:'y'},
    {x:.55, y:.18, c:'r'}, {x:.68, y:.52, c:'g'},
    {x:.82, y:.34, c:'y'}
  ];
  points.forEach(p=>{
    const d = document.createElement('div');
    d.style.cssText = `
      position:absolute; left:${p.x*w-7}px; top:${p.y*h-7}px;
      width:14px;height:14px;border-radius:50%;
      background:${p.c==='g'?'#22c55e':p.c==='y'?'#f59e0b':'#ef4444'};
      box-shadow:0 4px 12px rgba(0,0,0,.15);
      border:2px solid rgba(255,255,255,.9);
    `;
    el.appendChild(d);
  });
})();

// ===== (선택) DRF 연동 예시 =====
// const API = "/api";
// async function loadKPIs(){
//   const r = await fetch(`${API}/cafes/resident-populations/`);
//   const rows = await r.json();
//   document.getElementById('k_store').textContent = rows.length.toLocaleString();
// }
// loadKPIs();
