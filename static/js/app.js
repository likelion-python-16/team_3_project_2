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
});