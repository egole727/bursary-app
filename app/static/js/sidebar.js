document.addEventListener('DOMContentLoaded', function() {
    // Get all sidebar toggle buttons
    const sidebarToggles = document.querySelectorAll('.sidebar-toggle');
    
    // Add click event listener to each toggle button
    sidebarToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-mobile-open');
        });
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 992) {  // Only on mobile
            const sidebar = document.querySelector('.sidebar');
            const toggles = Array.from(document.querySelectorAll('.sidebar-toggle'));
            
            // Check if click is outside sidebar and not on toggle button
            if (!sidebar.contains(e.target) && !toggles.some(toggle => toggle.contains(e.target))) {
                document.body.classList.remove('sidebar-mobile-open');
            }
        }
    });
});
