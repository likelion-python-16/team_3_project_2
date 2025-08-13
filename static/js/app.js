

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

// ===== Authentication System =====
class AuthSystem {
  constructor() {
    this.isLoggedIn = false;
    this.userInfo = null;
    this.token = localStorage.getItem('auth_token');
    
    this.initializeUI();
    this.checkAuthStatus();
  }
  
  initializeUI() {
    // 로그인 다이얼로그 이벤트
    const dlg = document.getElementById('dlgLogin');
    ['btnOpenLogin','btnOpenLogin2','btnOpenLogin3','btnOpenLogin4'].forEach(id=>{
      const el = document.getElementById(id);
      if(el) el.onclick = ()=>dlg.showModal();
    });
    
    // 로그인 버튼 이벤트
    document.getElementById('btnLogin')?.addEventListener('click', async (e)=>{
      e.preventDefault();
      await this.login();
    });
    
    // 로그아웃 버튼 이벤트
    document.getElementById('btnLogout')?.addEventListener('click', async (e)=>{
      e.preventDefault();
      await this.logout();
    });
  }
  
  async checkAuthStatus() {
    if (this.token) {
      try {
        const response = await fetch('/api/accounts/users/me/', {
          headers: {
            'Authorization': `Token ${this.token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.userInfo = data.user;
          this.isLoggedIn = true;
          this.updateUI();
          return true;
        } else {
          // 토큰이 유효하지 않으면 제거
          localStorage.removeItem('auth_token');
          this.token = null;
        }
      } catch (error) {
        console.error('인증 상태 확인 실패:', error);
        localStorage.removeItem('auth_token');
        this.token = null;
      }
    }
    
    this.updateUI();
    return false;
  }
  
  async login() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const statusEl = document.getElementById('loginStatus');
    
    if (!email || !password) {
      this.showLoginStatus('이메일과 비밀번호를 입력해주세요.', 'error');
      return;
    }
    
    try {
      statusEl.textContent = '로그인 중...';
      statusEl.className = 'login-status';
      
      const response = await fetch('/api/accounts/users/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 토큰 저장
        this.token = data.token;
        localStorage.setItem('auth_token', this.token);
        
        // 사용자 정보 저장
        this.userInfo = data.user;
        this.isLoggedIn = true;
        
        this.showLoginStatus('로그인 성공!', 'success');
        
        setTimeout(() => {
          document.getElementById('dlgLogin').close();
          this.updateUI();
          // 지도 데이터 새로고침
          if (window.mapFilter) {
            window.mapFilter.loadMapData();
          }
        }, 1000);
        
      } else {
        this.showLoginStatus(data.message, 'error');
      }
      
    } catch (error) {
      console.error('로그인 실패:', error);
      this.showLoginStatus('로그인 중 오류가 발생했습니다.', 'error');
    }
  }
  
  async logout() {
    try {
      if (this.token) {
        await fetch('/api/accounts/users/logout/', {
          method: 'POST',
          headers: {
            'Authorization': `Token ${this.token}`,
            'Content-Type': 'application/json'
          }
        });
      }
    } catch (error) {
      console.error('로그아웃 API 실패:', error);
    }
    
    // 로컬 상태 초기화
    this.isLoggedIn = false;
    this.userInfo = null;
    this.token = null;
    localStorage.removeItem('auth_token');
    
    this.updateUI();
    
    // 폼 초기화
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
    document.getElementById('loginStatus').textContent = '';
  }
  
  showLoginStatus(message, type) {
    const statusEl = document.getElementById('loginStatus');
    statusEl.textContent = message;
    statusEl.className = `login-status ${type}`;
  }
  
  updateUI() {
    // 네비게이션 상태 업데이트
    const loggedOutNav = document.getElementById('nav-logged-out');
    const loggedInNav = document.getElementById('nav-logged-in');
    
    if (this.isLoggedIn && this.userInfo) {
      loggedOutNav.style.display = 'none';
      loggedInNav.style.display = 'flex';
      
      // 사용자 정보 표시
      document.getElementById('user-name').textContent = this.userInfo.username;
      document.getElementById('user-role').textContent = this.userInfo.role;
      
      // 탭 노트 업데이트
      document.getElementById('preview-note').style.display = 'none';
      document.getElementById('full-access-note').style.display = 'block';
      
      // 알림 패널 업데이트
      document.getElementById('login-required-notice').style.display = 'none';
      document.getElementById('logged-in-notice').style.display = 'block';
      
      // 로그인 상태에서 추가 기능 활성화
      
    } else {
      loggedOutNav.style.display = 'flex';
      loggedInNav.style.display = 'none';
      
      // 탭 노트 업데이트
      document.getElementById('preview-note').style.display = 'block';
      document.getElementById('full-access-note').style.display = 'none';
      
      // 알림 패널 업데이트
      document.getElementById('login-required-notice').style.display = 'block';
      document.getElementById('logged-in-notice').style.display = 'none';
      
      // 비로그인 상태
    }
  }
  
  getAuthHeaders() {
    if (this.token) {
      return {
        'Authorization': `Token ${this.token}`,
        'Content-Type': 'application/json'
      };
    }
    return {
      'Content-Type': 'application/json'
    };
  }
}

// 전역 인증 시스템 인스턴스
let authSystem;

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

// ===== Filter & Map Integration =====
const API = "/api";

class MapFilter {
  constructor() {
    this.filters = {
      region: '마포구',
      majorCategory: '전체',
      midCategory: '전체',
      franchise: null
    };
    
    this.initializeEventListeners();
    this.loadMapData(); // 초기 데이터 로드
  }
  
  initializeEventListeners() {
    // 드롭다운 필터 이벤트
    document.getElementById('selRegion').addEventListener('change', (e) => {
      this.filters.region = e.target.value;
      this.updateMapTitle();
      this.loadMapData();
    });
    
    document.getElementById('selMajor').addEventListener('change', (e) => {
      this.filters.majorCategory = e.target.value;
      this.loadMapData();
    });
    
    document.getElementById('selMid').addEventListener('change', (e) => {
      this.filters.midCategory = e.target.value;
      this.loadMapData();
    });
    
    // 프랜차이즈 칩 클릭 이벤트
    document.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        // 기존 선택 해제
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('selected'));
        
        // 새로운 선택
        if (this.filters.franchise === e.target.textContent) {
          // 같은 칩을 다시 클릭하면 해제
          this.filters.franchise = null;
        } else {
          e.target.classList.add('selected');
          this.filters.franchise = e.target.textContent;
        }
        
        this.loadMapData();
      });
    });
  }
  
  updateMapTitle() {
    const titleElement = document.querySelector('#pane-map .card__head h3');
    const tagElement = document.querySelector('#pane-map .card__head .tag');
    if (titleElement) {
      titleElement.innerHTML = `${this.filters.region} 상권 지도 <span class="tag">${this.getFilterDescription()}</span>`;
    }
  }
  
  getFilterDescription() {
    const parts = [];
    if (this.filters.majorCategory !== '전체') parts.push(this.filters.majorCategory);
    if (this.filters.midCategory !== '전체') parts.push(this.filters.midCategory);
    if (this.filters.franchise) parts.push(this.filters.franchise);
    
    return parts.length > 0 ? parts.join(' · ') + ' 분석 결과' : '전체 업종 분석 결과';
  }
  
  async loadMapData() {
    // 모든 사용자가 데이터를 볼 수 있도록 변경
    // 로그인 여부에 따라 다른 데이터 제공
    
    try {
      const params = new URLSearchParams();
      if (this.filters.region) params.append('region', this.filters.region);
      if (this.filters.majorCategory) params.append('major_category', this.filters.majorCategory);
      if (this.filters.midCategory) params.append('mid_category', this.filters.midCategory);
      if (this.filters.franchise) params.append('franchise', this.filters.franchise);
      
      const response = await fetch(`${API}/cafes/cafes/filtered_data/?${params}`, {
        headers: authSystem.getAuthHeaders()
      });
      
      if (response.status === 401) {
        // 인증이 만료된 경우
        authSystem.logout();
        this.showDemoData();
        return;
      }
      
      const data = await response.json();
      
      // 비로그인 사용자도 데이터를 볼 수 있도록 변경
      // 로그인 사용자는 추가 기능 이용 가능
      
      if (authSystem && authSystem.isLoggedIn) {
        // 로그인 사용자: 실제 데이터 표시
        this.updateMap(data.map_data);
        this.updateStatistics(data.statistics);
      } else {
        // 비로그인 사용자: 데모 데이터 표시
        this.updateMap(this.getDemoMapData());
        this.updateStatistics(this.getDemoStatistics());
      }
      
    } catch (error) {
      console.error('데이터 로드 실패:', error);
      // 에러 시 데모 데이터 표시
      this.showDemoData();
    }
  }
  
  getDemoMapData() {
    // 데모 맵 데이터 반환
    return [
      { x: 1, y: 1, status: 'good', shops: 45, growth: 8.5 },
      { x: 2, y: 1, status: 'warning', shops: 32, growth: -2.1 },
      { x: 3, y: 1, status: 'good', shops: 28, growth: 12.3 },
      { x: 1, y: 2, status: 'good', shops: 52, growth: 15.7 },
      { x: 2, y: 2, status: 'danger', shops: 18, growth: -8.4 }
    ];
  }
  
  getDemoStatistics() {
    // 데모 통계 데이터 반환
    return {
      total_shops: 175,
      avg_growth: 5.2,
      danger_zones: 1,
      new_businesses: 23
    };
  }
  
  updateMap(mapData) {
    const mapElement = document.getElementById('gridMap');
    if (!mapElement) return;
    
    // 기존 점들 제거
    mapElement.innerHTML = '';
    
    if (mapData.length === 0) {
      // 데이터가 없을 때 메시지 표시
      const noDataMsg = document.createElement('div');
      noDataMsg.style.cssText = `
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        color: #666; font-size: 14px; text-align: center;
      `;
      noDataMsg.textContent = '선택한 조건에 맞는 카페가 없습니다.';
      mapElement.appendChild(noDataMsg);
      return;
    }
    
    const w = mapElement.clientWidth;
    const h = mapElement.clientHeight;
    
    // 위도/경도 범위 계산 (정규화를 위해)
    const lats = mapData.map(d => d.latitude);
    const lngs = mapData.map(d => d.longitude);
    const latMin = Math.min(...lats), latMax = Math.max(...lats);
    const lngMin = Math.min(...lngs), lngMax = Math.max(...lngs);
    
    mapData.forEach((cafe, index) => {
      // 위도/경도를 맵 좌표로 변환
      const x = lngMax !== lngMin ? (cafe.longitude - lngMin) / (lngMax - lngMin) : 0.5;
      const y = latMax !== latMin ? 1 - (cafe.latitude - latMin) / (latMax - latMin) : 0.5;
      
      const dot = document.createElement('div');
      const color = this.getStatusColor(cafe.status);
      
      dot.style.cssText = `
        position: absolute; 
        left: ${x * w - 8}px; 
        top: ${y * h - 8}px;
        width: 16px; height: 16px; border-radius: 50%;
        background: ${color};
        box-shadow: 0 4px 12px rgba(0,0,0,.15);
        border: 2px solid rgba(255,255,255,.9);
        cursor: pointer;
        transition: transform 0.2s;
      `;
      
      // 호버 효과
      dot.addEventListener('mouseenter', () => {
        dot.style.transform = 'scale(1.3)';
        this.showTooltip(dot, cafe);
      });
      
      dot.addEventListener('mouseleave', () => {
        dot.style.transform = 'scale(1)';
        this.hideTooltip();
      });
      
      mapElement.appendChild(dot);
    });
  }
  
  getStatusColor(status) {
    switch(status) {
      case 'safe': return '#22c55e';
      case 'warning': return '#f59e0b';
      case 'risk': return '#ef4444';
      default: return '#6b7280';
    }
  }
  
  showTooltip(element, cafe) {
    const tooltip = document.createElement('div');
    tooltip.id = 'map-tooltip';
    tooltip.style.cssText = `
      position: absolute;
      background: rgba(0,0,0,0.8);
      color: white;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      pointer-events: none;
      z-index: 1000;
      white-space: nowrap;
    `;
    
    tooltip.innerHTML = `
      <strong>${cafe.name}</strong><br>
      ${cafe.address}<br>
      교통량: ${cafe.population_data.traffic_level}
    `;
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = (rect.left + 20) + 'px';
    tooltip.style.top = (rect.top - 50) + 'px';
    
    document.body.appendChild(tooltip);
  }
  
  hideTooltip() {
    const tooltip = document.getElementById('map-tooltip');
    if (tooltip) tooltip.remove();
  }
  
  updateStatistics(stats) {
    // KPI 업데이트
    const elements = {
      'k_cnt': stats.total_cafes,
      'k_store': stats.total_businesses
    };
    
    Object.entries(elements).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) {
        el.textContent = value.toLocaleString();
      }
    });
    
    // 다른 통계들도 업데이트
    const kpiElements = document.querySelectorAll('#pane-map .kpi .v');
    if (kpiElements[1]) kpiElements[1].textContent = stats.total_businesses;
    if (kpiElements[3]) kpiElements[3].textContent = stats.risk_areas;
  }
  
  showDemoData() {
    // 기존 데모 데이터 표시 로직
    const el = document.getElementById('gridMap');
    if (!el) return;
    
    el.innerHTML = '';
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
  }
}

// 칩 선택 스타일 추가
const style = document.createElement('style');
style.textContent = `
  .chip.selected {
    background: #3b82f6 !important;
    color: white !important;
    font-weight: bold;
  }
  .chip {
    cursor: pointer;
    transition: all 0.2s;
  }
  .chip:hover {
    opacity: 0.8;
  }
`;
document.head.appendChild(style);

// 페이지 로드 시 시스템 초기화
let mapFilter;
document.addEventListener('DOMContentLoaded', () => {
  // 인증 시스템 먼저 초기화
  authSystem = new AuthSystem();
  
  // 약간의 지연 후 지도 필터 초기화 (인증 상태 확인 후)
  setTimeout(() => {
    mapFilter = new MapFilter();
    // 전역 접근을 위해 window에 등록
    window.mapFilter = mapFilter;
  }, 100);
});
