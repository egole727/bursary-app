document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarToggles = document.querySelectorAll('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const mainWrapper = document.querySelector('.main-wrapper');
    const navbar = document.querySelector('.navbar');

    sidebarToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            mainWrapper.classList.toggle('sidebar-open');
            navbar.classList.toggle('sidebar-open');
        });
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth < 992 && 
            !event.target.closest('.sidebar') && 
            !event.target.closest('.sidebar-toggle') && 
            sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            mainWrapper.classList.remove('sidebar-open');
            navbar.classList.remove('sidebar-open');
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
