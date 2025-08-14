document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab');
    const contentPane = document.getElementById('content-pane');

    const paneUrls = {
        map: "/cafes/pane/map/",
        franchise: "/cafes/pane/franchise/",
        trend: "/cafes/pane/trend/",
        report: "/cafes/pane/report/",
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active class on tabs
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Change iframe src
            const paneName = tab.dataset.tab;
            if (contentPane && paneUrls[paneName]) {
                contentPane.src = paneUrls[paneName];
            }
        });
    });
});