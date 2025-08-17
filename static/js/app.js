document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab');
    const contentPane = document.getElementById('content-pane');
    const selRegion = document.getElementById('selRegion');

    const paneUrls = {
        map: "/cafes/pane/map/",
        franchise: "/cafes/pane/franchise/",
        trend: "/cafes/pane/trend/",
        report: "/cafes/pane/report/",
    };

    // 지역 선택에서 현재 선택된 지역 파라미터를 가져오는 함수
    function getCurrentRegionParam() {
        if (selRegion) {
            const selectedOption = selRegion.options[selRegion.selectedIndex];
            return selectedOption ? selectedOption.text : '';
        }
        return '';
    }

    // 업종 대분류 선택값을 가져오는 함수
    function getCurrentMajorCategoryParam() {
        const selMajor = document.getElementById('selMajor');
        if (selMajor) {
            return selMajor.value;
        }
        return '';
    }

    // 업종 중분류 선택값을 가져오는 함수
    function getCurrentMidCategoryParam() {
        const selMid = document.getElementById('selMid');
        if (selMid) {
            const selectedOption = selMid.options[selMid.selectedIndex];
            return selectedOption ? selectedOption.text : '';
        }
        return '';
    }

    // Function to update iframe src with all filter parameters
    function updateIframeSrc(baseUrl) {
        const params = new URLSearchParams();
        
        const regionText = getCurrentRegionParam();
        if (regionText) {
            params.append('region', regionText);
        }
        
        const majorCategory = getCurrentMajorCategoryParam();
        if (majorCategory) {
            params.append('major_category', majorCategory);
        }
        
        const midCategory = getCurrentMidCategoryParam();
        if (midCategory) {
            params.append('mid_category', midCategory);
        }
        
        const queryString = params.toString();
        return queryString ? `${baseUrl}?${queryString}` : baseUrl;
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active class on tabs
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Change iframe src
            const paneName = tab.dataset.tab;
            if (contentPane && paneUrls[paneName]) {
                contentPane.src = updateIframeSrc(paneUrls[paneName]);
            }
        });
    });

    // Function to update current pane with new filters
    function updateCurrentPane() {
        const activeTab = document.querySelector('.tab.active');
        if (activeTab && contentPane) {
            const paneName = activeTab.dataset.tab;
            if (paneUrls[paneName]) {
                contentPane.src = updateIframeSrc(paneUrls[paneName]);
            }
        }
    }

    // Add event listeners for all filter changes
    if (selRegion) {
        selRegion.addEventListener('change', updateCurrentPane);

        // Set initial region parameter for the default map pane
        if (contentPane && contentPane.src.includes('/cafes/pane/map/')) {
            contentPane.src = updateIframeSrc(paneUrls.map);
        }
    }

    // Add event listeners for major and mid category changes
    const selMajor = document.getElementById('selMajor');
    const selMid = document.getElementById('selMid');
    
    if (selMajor) {
        selMajor.addEventListener('change', updateCurrentPane);
    }
    
    if (selMid) {
        selMid.addEventListener('change', updateCurrentPane);
    }
    
    // 프랜차이즈 칩 클릭 이벤트 추가
    const franchiseChips = document.querySelectorAll('.chip');
    franchiseChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const franchiseType = chip.textContent.trim();
            window.location.href = `/summary/?franchise_type=${encodeURIComponent(franchiseType)}`;
        });
    });
    
    // 페이지 버튼 이벤트 리스너
    const btnStart = document.getElementById('btnStart');
    const btnTry = document.getElementById('btnTry');
    const btnMyAccount = document.getElementById('btnMyAccount');
    const btnPricing = document.getElementById('btnPricing');
    
    if (btnStart) {
        btnStart.addEventListener('click', () => {
            window.location.href = '/start/';
        });
    }
    
    if (btnTry) {
        btnTry.addEventListener('click', () => {
            window.location.href = '/summary/';
        });
    }
    
    if (btnMyAccount) {
        btnMyAccount.addEventListener('click', () => {
            window.location.href = '/account/';
        });
    }
    
    if (btnPricing) {
        btnPricing.addEventListener('click', () => {
            // 회원가입 페이지로 이동
            window.location.href = '/register/';
        });
    }
});

// 요금제 모달 표시
function showPricingModal() {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 32px; max-width: 1000px; margin: 20px;">
            <h3 style="margin: 0 0 24px 0;">💎 요금제 안내</h3>
            
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #6b7280;">무료 플랜</h4>
                <div style="font-size: 24px; font-weight: bold; margin-bottom: 12px;">₩0 <span style="font-size: 14px; color: #6b7280;">/월</span></div>
                <ul style="margin: 0; padding-left: 20px; color: #374151;">
                    <li>일일 분석 조회 10회</li>
                    <li>기본 상권 분석</li>
                    <li>커뮤니티 지원</li>
                </ul>
            </div>
            
            <div style="border: 2px solid #3b82f6; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                <h4 style="margin: 0 0 12px 0; color: #3b82f6;">프리미엄 플랜 ⭐</h4>
                <div style="font-size: 24px; font-weight: bold; margin-bottom: 12px; color: #3b82f6;">₩9,500 <span style="font-size: 14px; color: #6b7280;">/월</span></div>
                <ul style="margin: 0; padding-left: 20px; color: #374151;">
                    <li>무제한 분석 조회</li>
                    <li>상세 지역별 분석</li>
                    <li>AI 투자 추천</li>
                    <li>데이터 내보내기</li>
                    <li>우선 고객 지원</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <button onclick="window.location.href='/start/'" style="background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; margin-right: 12px; cursor: pointer;">시작하기</button>
                <button onclick="this.closest('[style*=fixed]').remove()" style="background: #6b7280; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer;">닫기</button>
            </div>
        </div>
    `;
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    document.body.appendChild(modal);
}