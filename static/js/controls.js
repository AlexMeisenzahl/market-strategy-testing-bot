// Controls.js - Bot control functions

// Control bot (start/pause/stop/restart)
async function controlBot(action) {
    try {
        const response = await fetch(`/api/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message, 'success');
            
            // Update UI immediately
            setTimeout(() => {
                loadStatus();
            }, 500);
        } else {
            showToast('Error: ' + data.message, 'error');
        }
    } catch (error) {
        console.error(`Error ${action} bot:`, error);
        showToast(`Error ${action} bot`, 'error');
    }
}
