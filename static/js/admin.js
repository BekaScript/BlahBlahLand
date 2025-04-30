// Admin panel initialization
document.addEventListener("DOMContentLoaded", function() {
  initAdminPanel();
});

function initAdminPanel() {
  // Initialize navigation
  initNavigation();
  
  // Load dashboard stats
  loadDashboardStats();
  
  // Load users data
  loadUsers();
  
  // Initialize search functionality
  initSearch();
  
  // Initialize modals
  initModals();
  
  // Initialize content moderation
  initContentModeration();
  
  // Initialize logout
  initLogout();
}

// Navigation between sections
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.admin-section');
  
  navItems.forEach(item => {
    item.addEventListener('click', function() {
      // Ignore if logout button
      if (item.classList.contains('logout')) {
        return;
      }
      
      // Remove active class from all items
      navItems.forEach(i => i.classList.remove('active'));
      
      // Add active class to clicked item
      item.classList.add('active');
      
      // Hide all sections
      sections.forEach(section => {
        section.classList.remove('active');
      });
      
      // Show selected section
      const sectionId = item.getAttribute('data-section') + '-section';
      document.getElementById(sectionId).classList.add('active');
    });
  });
}

// Load dashboard statistics
function loadDashboardStats() {
  // Fetch total users count
  fetch('/api/admin/stats/users')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('total-users-count').textContent = data.count;
      } else {
        document.getElementById('total-users-count').textContent = 'Error';
      }
    })
    .catch(error => {
      console.error('Error loading user stats:', error);
      document.getElementById('total-users-count').textContent = 'Error';
    });
  
  // Fetch total groups count
  fetch('/api/admin/stats/groups')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('total-groups-count').textContent = data.count;
      } else {
        document.getElementById('total-groups-count').textContent = 'Error';
      }
    })
    .catch(error => {
      console.error('Error loading group stats:', error);
      document.getElementById('total-groups-count').textContent = 'Error';
    });
  
  // Fetch total messages count
  fetch('/api/admin/stats/messages')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('total-messages-count').textContent = data.count;
      } else {
        document.getElementById('total-messages-count').textContent = 'Error';
      }
    })
    .catch(error => {
      console.error('Error loading message stats:', error);
      document.getElementById('total-messages-count').textContent = 'Error';
    });
}

// Load users for the user management section
function loadUsers() {
  const usersTableBody = document.getElementById('users-table-body');
  
  fetch('/api/admin/users')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.users) {
        // Clear the loading message
        usersTableBody.innerHTML = '';
        
        // Add each user to the table
        data.users.forEach(user => {
          const tr = document.createElement('tr');
          
          // Status label
          const statusLabel = user.is_banned ? 
            '<span class="status-label status-banned">Banned</span>' : 
            '<span class="status-label status-active">Active</span>';
          
          // Action buttons
          const banButtonText = user.is_banned ? 'Unban' : 'Ban';
          const banButtonClass = user.is_banned ? 'primary' : 'ban-btn';
          
          tr.innerHTML = `
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${statusLabel}</td>
            <td>
              <button class="action-btn ${banButtonClass}" data-userid="${user.id}" data-username="${user.username}" data-action="${user.is_banned ? 'unban' : 'ban'}">${banButtonText}</button>
              <button class="action-btn delete-btn" data-userid="${user.id}" data-username="${user.username}" data-action="delete">Delete</button>
            </td>
          `;
          
          usersTableBody.appendChild(tr);
        });
        
        // Add event listeners to action buttons
        addUserActionListeners();
      } else {
        usersTableBody.innerHTML = '<tr><td colspan="4" class="loading-data">Failed to load users data</td></tr>';
      }
    })
    .catch(error => {
      console.error('Error loading users:', error);
      usersTableBody.innerHTML = '<tr><td colspan="4" class="loading-data">Failed to load users data</td></tr>';
    });
}

// Add event listeners to user action buttons
function addUserActionListeners() {
  // Ban/Unban buttons
  document.querySelectorAll('.action-btn[data-action="ban"], .action-btn[data-action="unban"]').forEach(button => {
    button.addEventListener('click', function() {
      const userId = this.getAttribute('data-userid');
      const username = this.getAttribute('data-username');
      const action = this.getAttribute('data-action');
      
      if (action === 'ban') {
        openBanModal(userId, username);
      } else {
        // Directly unban the user
        unbanUser(userId);
      }
    });
  });
  
  // Delete buttons
  document.querySelectorAll('.action-btn[data-action="delete"]').forEach(button => {
    button.addEventListener('click', function() {
      const userId = this.getAttribute('data-userid');
      const username = this.getAttribute('data-username');
      
      openDeleteModal(userId, username);
    });
  });
}

// Initialize search functionality
function initSearch() {
  const userSearchInput = document.getElementById('user-search');
  
  if (userSearchInput) {
    userSearchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase();
      const tableRows = document.querySelectorAll('#users-table-body tr');
      
      tableRows.forEach(row => {
        const username = row.querySelector('td:first-child').textContent.toLowerCase();
        const email = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        
        if (username.includes(searchTerm) || email.includes(searchTerm)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }
}

// Initialize modals
function initModals() {
  // Close modal buttons
  document.querySelectorAll('.close-modal, .btn.secondary').forEach(button => {
    button.addEventListener('click', function() {
      const modal = this.closest('.modal');
      if (modal) {
        modal.style.display = 'none';
      }
    });
  });
  
  // Confirm ban button
  const confirmBanBtn = document.getElementById('confirm-ban');
  if (confirmBanBtn) {
    confirmBanBtn.addEventListener('click', function() {
      const userId = this.getAttribute('data-userid');
      banUser(userId);
    });
  }
  
  // Confirm delete button
  const confirmDeleteBtn = document.getElementById('confirm-delete');
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', function() {
      const userId = this.getAttribute('data-userid');
      deleteUser(userId);
    });
  }
}

// Open ban user modal
function openBanModal(userId, username) {
  const modal = document.getElementById('ban-user-modal');
  const usernameSpan = document.getElementById('ban-username');
  const confirmButton = document.getElementById('confirm-ban');
  
  usernameSpan.textContent = username;
  confirmButton.setAttribute('data-userid', userId);
  
  modal.style.display = 'flex';
}

// Open delete user modal
function openDeleteModal(userId, username) {
  const modal = document.getElementById('delete-user-modal');
  const usernameSpan = document.getElementById('delete-username');
  const confirmButton = document.getElementById('confirm-delete');
  
  usernameSpan.textContent = username;
  confirmButton.setAttribute('data-userid', userId);
  
  modal.style.display = 'flex';
}

// Ban a user
function banUser(userId) {
  fetch(`/api/admin/users/${userId}/ban`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Close the modal
        document.getElementById('ban-user-modal').style.display = 'none';
        
        // Reload users to update the UI
        loadUsers();
      } else {
        alert('Failed to ban user: ' + (data.message || 'Unknown error'));
      }
    })
    .catch(error => {
      console.error('Error banning user:', error);
      alert('Failed to ban user. Please try again.');
    });
}

// Unban a user
function unbanUser(userId) {
  fetch(`/api/admin/users/${userId}/unban`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Reload users to update the UI
        loadUsers();
      } else {
        alert('Failed to unban user: ' + (data.message || 'Unknown error'));
      }
    })
    .catch(error => {
      console.error('Error unbanning user:', error);
      alert('Failed to unban user. Please try again.');
    });
}

// Delete a user
function deleteUser(userId) {
  fetch(`/api/admin/users/${userId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Close the modal
        document.getElementById('delete-user-modal').style.display = 'none';
        
        // Reload users to update the UI
        loadUsers();
      } else {
        alert('Failed to delete user: ' + (data.message || 'Unknown error'));
      }
    })
    .catch(error => {
      console.error('Error deleting user:', error);
      alert('Failed to delete user. Please try again.');
    });
}

// Initialize content moderation (previously settings)
function initContentModeration() {
  // Save blocked hashtags
  const saveHashtagsBtn = document.getElementById('save-hashtags');
  if (saveHashtagsBtn) {
    saveHashtagsBtn.addEventListener('click', function() {
      const hashtags = document.getElementById('blocked-hashtags').value;
      
      fetch('/api/admin/settings/blocked-hashtags', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          hashtags: hashtags.split(',').map(tag => tag.trim())
        })
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            alert('Blocked hashtags saved successfully');
          } else {
            alert('Failed to save blocked hashtags: ' + (data.message || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error saving blocked hashtags:', error);
          alert('Failed to save blocked hashtags. Please try again.');
        });
    });
  }
  
  // Toggle AI moderation
  const aiToggle = document.getElementById('ai-moderation-toggle');
  if (aiToggle) {
    // Load current setting
    fetch('/api/admin/settings/ai-moderation')
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          aiToggle.checked = data.enabled;
        }
      })
      .catch(error => {
        console.error('Error loading AI moderation setting:', error);
      });
    
    // Handle toggle change
    aiToggle.addEventListener('change', function() {
      const enabled = this.checked;
      
      fetch('/api/admin/settings/ai-moderation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          enabled: enabled
        })
      })
        .then(response => response.json())
        .then(data => {
          if (!data.success) {
            alert('Failed to update AI moderation setting: ' + (data.message || 'Unknown error'));
            // Revert toggle if failed
            this.checked = !enabled;
          }
        })
        .catch(error => {
          console.error('Error updating AI moderation setting:', error);
          alert('Failed to update AI moderation setting. Please try again.');
          // Revert toggle if failed
          this.checked = !enabled;
        });
    });
  }
  
  // Load blocked hashtags
  loadBlockedHashtags();
}

// Initialize logout
function initLogout() {
  const logoutBtn = document.querySelector('.nav-item.logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
      fetch('/api/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            window.location.href = '/login';
          } else {
            alert('Failed to log out: ' + (data.message || 'Unknown error'));
          }
        })
        .catch(error => {
          console.error('Error logging out:', error);
          alert('Failed to log out. Please try again.');
        });
    });
  }
}

// Load blocked hashtags from server
function loadBlockedHashtags() {
  const blockedHashtagsTextarea = document.getElementById('blocked-hashtags');
  if (!blockedHashtagsTextarea) return;
  
  fetch('/api/admin/settings/blocked-hashtags')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.hashtags) {
        blockedHashtagsTextarea.value = data.hashtags.join(', ');
      }
    })
    .catch(error => {
      console.error('Error loading blocked hashtags:', error);
    });
} 