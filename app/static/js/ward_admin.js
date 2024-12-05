function deleteWardAdmin(id) {
    if (confirm('Are you sure you want to delete this ward admin? This action cannot be undone.')) {
        fetch(`/admin/ward-admin/${id}/delete`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error deleting ward admin');
            }
        });
    }
} 