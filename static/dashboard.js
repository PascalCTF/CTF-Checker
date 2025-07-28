// Dashboard JavaScript functionality

let refreshInterval;
let lastUpdateTime = new Date();

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Start auto-refresh
    startAutoRefresh();
    
    // Initial status refresh
    refreshStatus();
    
    // Update last update time display
    updateLastUpdateDisplay();
    setInterval(updateLastUpdateDisplay, 1000);
});

// Auto-refresh functionality
function startAutoRefresh() {
    // Refresh every 30 seconds
    refreshInterval = setInterval(refreshStatus, 30000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Refresh checker status
async function refreshStatus() {
    try {
        const response = await fetch('/api/checker_status');
        if (!response.ok) {
            throw new Error('Failed to fetch status');
        }
        
        const checkers = await response.json();
        updateCheckersTable(checkers);
        lastUpdateTime = new Date();
        
    } catch (error) {
        console.error('Error refreshing status:', error);
        showNotification('Failed to refresh status', 'error');
    }
}

// Update checkers table with new data
function updateCheckersTable(checkers) {
    const tableBody = document.getElementById('checkers-table');
    if (!tableBody) return;
    
    checkers.forEach(checker => {
        const row = tableBody.querySelector(`tr[data-checker-id="${checker.id}"]`);
        if (!row) return;
        
        // Update status indicator
        const statusIndicator = row.querySelector('.status-indicator');
        const statusText = row.querySelector('.status-text');
        
        if (statusIndicator && statusText) {
            // Remove old status classes
            statusIndicator.className = 'status-indicator';
            statusIndicator.classList.add(`status-${checker.status}`);
            statusText.textContent = capitalizeFirst(checker.status);
            
            // Add animation if status changed
            if (statusText.dataset.lastStatus !== checker.status) {
                row.classList.add('status-updated');
                setTimeout(() => row.classList.remove('status-updated'), 2000);
                statusText.dataset.lastStatus = checker.status;
            }
        }
        
        // Update last run time
        const lastRunElement = row.querySelector('.last-run-time');
        if (lastRunElement && checker.last_run) {
            const lastRunDate = new Date(checker.last_run);
            lastRunElement.textContent = formatDateTime(lastRunDate);
        }
        
        // Update status icon
        const nameCell = row.children[1];
        const existingIcon = nameCell.querySelector('.fas');
        if (existingIcon) existingIcon.remove();
        
        let iconClass = '';
        let iconColor = '';
        
        switch (checker.status) {
            case 'success':
                iconClass = 'fas fa-check-circle';
                iconColor = 'text-success';
                break;
            case 'failure':
                iconClass = 'fas fa-times-circle';  
                iconColor = 'text-danger';
                break;
            case 'error':
                iconClass = 'fas fa-exclamation-triangle';
                iconColor = 'text-warning';
                break;
        }
        
        if (iconClass) {
            const icon = document.createElement('i');
            icon.className = `${iconClass} ${iconColor} ms-1`;
            nameCell.appendChild(icon);
        }
    });
}

// Show checker details modal
async function showCheckerDetails(checkerId) {
    const modal = new bootstrap.Modal(document.getElementById('checkerDetailsModal'));
    const content = document.getElementById('checkerDetailsContent');
    
    // Show loading state
    content.innerHTML = `
        <div class="text-center py-3">
            <div class="loading-spinner"></div>
            <p class="mt-2">Loading details...</p>
        </div>
    `;
    
    modal.show();
    
    try {
        const response = await fetch(`/api/checker_status`);
        const checkers = await response.json();
        const checker = checkers.find(c => c.id === checkerId);
        
        if (!checker) {
            throw new Error('Checker not found');
        }
        
        // Display checker details
        content.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-info-circle me-2"></i>Basic Information</h6>
                    <table class="table table-sm">
                        <tr>
                            <td><strong>Name:</strong></td>
                            <td>${escapeHtml(checker.name)}</td>
                        </tr>
                        <tr>
                            <td><strong>Status:</strong></td>
                            <td>
                                <span class="status-indicator status-${checker.status}"></span>
                                ${capitalizeFirst(checker.status)}
                            </td>
                        </tr>
                        <tr>
                            <td><strong>Active:</strong></td>
                            <td>${checker.is_active ? 'Yes' : 'No'}</td>
                        </tr>
                        <tr>
                            <td><strong>Last Run:</strong></td>
                            <td>${checker.last_run ? formatDateTime(new Date(checker.last_run)) : 'Never'}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-terminal me-2"></i>Recent Output</h6>
                    <pre class="bg-dark text-light p-2 rounded" style="max-height: 200px; overflow-y: auto; font-size: 0.8rem;">${escapeHtml(checker.recent_output || 'No recent output')}</pre>
                    ${checker.error_message ? `
                        <h6 class="mt-3 text-warning"><i class="fas fa-exclamation-triangle me-2"></i>Error Message</h6>
                        <div class="alert alert-warning">
                            <small>${escapeHtml(checker.error_message)}</small>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading checker details:', error);
        content.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load checker details: ${error.message}
            </div>
        `;
    }
}

// Utility functions
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDateTime(date) {
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateLastUpdateDisplay() {
    const element = document.getElementById('last-update');
    if (!element) return;
    
    const now = new Date();
    const diff = Math.floor((now - lastUpdateTime) / 1000);
    
    let displayText = '';
    if (diff < 60) {
        displayText = `${diff}s ago`;
    } else if (diff < 3600) {
        displayText = `${Math.floor(diff / 60)}m ago`;
    } else {
        displayText = `${Math.floor(diff / 3600)}h ago`;
    }
    
    element.innerHTML = `<i class="fas fa-check me-1"></i>${displayText}`;
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Handle visibility change to pause/resume auto-refresh
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        startAutoRefresh();
        refreshStatus(); // Immediate refresh when page becomes visible
    } else {
        stopAutoRefresh();
    }
});
