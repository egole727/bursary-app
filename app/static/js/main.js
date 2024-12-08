document.addEventListener('DOMContentLoaded', function() {
    // Create backdrop element
    const backdrop = document.createElement('div');
    backdrop.className = 'sidebar-backdrop';
    document.body.appendChild(backdrop);
    
    // Handle sidebar toggle
    const toggles = document.querySelectorAll('.sidebar-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sidebar-open');
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('show');
        });
    });
    
    // Close sidebar when clicking backdrop
    backdrop.addEventListener('click', function() {
        document.body.classList.remove('sidebar-open');
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.remove('show');
    });
    
    // Close sidebar on window resize if in mobile view
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            document.body.classList.remove('sidebar-open');
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.remove('show');
        }
    });

    // Flash Messages Auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => message.remove(), 150);
        }, 5000);
    });
});
