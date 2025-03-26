// Global variables
let currentContact = null;
let currentGroup = null;

// Initialize chat functionality
document.addEventListener('DOMContentLoaded', () => {
    // Setup event listeners
    setupChatInput();
    setupMessageActions();
    
    // Load contacts list
    loadContacts();
});

// Load user's contacts
function loadContacts() {
    fetch('/api/contacts')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayContacts(data.contacts);
            }
        })
        .catch(error => {
            // Error handling for contacts
        });
}

// Display contacts in the sidebar
function displayContacts(contacts) {
    const usersList = document.getElementById('users');
    usersList.innerHTML = '';
    
    contacts.forEach(contact => {
        const contactElement = document.createElement('li');
        contactElement.className = 'user';
        contactElement.setAttribute('data-id', contact.id);
        contactElement.setAttribute('data-type', 'contact');
        
        contactElement.innerHTML = `
            <div class="user-info">
                <div class="user-name">${contact.display_name || contact.username}</div>
                <div class="last-message">${contact.last_message || ''}</div>
            </div>
        `;
        
        contactElement.addEventListener('click', () => {
            openChat(contact.id, 'contact');
        });
        
        usersList.appendChild(contactElement);
    });
    
    // Also load groups
    loadGroups();
}

// Load user's groups
function loadGroups() {
    fetch('/api/groups')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayGroups(data.groups);
            }
        })
        .catch(error => {
            // Error handling for groups
        });
}

// Display groups in the sidebar
function displayGroups(groups) {
    const usersList = document.getElementById('users');
    
    groups.forEach(group => {
        const groupElement = document.createElement('li');
        groupElement.className = 'user group';
        groupElement.setAttribute('data-id', group.id);
        groupElement.setAttribute('data-type', 'group');
        
        groupElement.innerHTML = `
            <div class="user-info">
                <div class="user-name">${group.name}</div>
                <div class="last-message">${group.last_message || ''}</div>
            </div>
        `;
        
        groupElement.addEventListener('click', () => {
            openChat(group.id, 'group');
        });
        
        usersList.appendChild(groupElement);
    });
}

// Open a chat with a contact or group
function openChat(id, type) {
    // Highlight selected chat
    document.querySelectorAll('#users .user').forEach(el => {
        el.classList.remove('active');
    });
    
    document.querySelector(`#users .user[data-id="${id}"][data-type="${type}"]`).classList.add('active');
    
    // Clear current chat
    document.getElementById('messages').innerHTML = '';
    
    // Update current chat target
    if (type === 'contact') {
        currentContact = id;
        currentGroup = null;
        document.getElementById('chat-header-title').textContent = document.querySelector(`#users .user[data-id="${id}"][data-type="contact"] .user-name`).textContent;
    } else {
        currentGroup = id;
        currentContact = null;
        document.getElementById('chat-header-title').textContent = document.querySelector(`#users .user[data-id="${id}"][data-type="group"] .user-name`).textContent;
    }
    
    // Show settings button
    document.getElementById('settings-btn').style.display = 'block';
    
    // Load messages
    loadMessages();
}

// Load messages for current chat
function loadMessages() {
    let url;
    if (currentContact) {
        url = `/api/messages?contact_id=${currentContact}`;
    } else if (currentGroup) {
        url = `/api/messages?group_id=${currentGroup}`;
    } else {
        return; // No chat selected
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayMessages(data.messages);
            }
        })
        .catch(error => {
            // Error handling for messages
        });
}

// Display messages in the chat window
function displayMessages(messages) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    
    messages.forEach(msg => {
        const messageElement = document.createElement('div');
        messageElement.className = msg.is_own_message ? 'message own' : 'message';
        messageElement.setAttribute('data-id', msg.id);
        
        let messageContent = `
            <div class="message-content">
                ${!msg.is_own_message && currentGroup ? `<div class="sender-name">${msg.sender_username}</div>` : ''}
                <div class="message-text">${msg.message}</div>
                <div class="message-time">${formatTime(msg.timestamp)}</div>
                ${msg.edited ? '<span class="edited-label">(edited)</span>' : ''}
            </div>
        `;
        
        messageElement.innerHTML = messageContent;
        
        // Add click event for own messages
        if (msg.is_own_message) {
            messageElement.addEventListener('click', () => {
                showMessageActions(msg.id);
            });
        }
        
        messagesContainer.appendChild(messageElement);
    });
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Format timestamp for display
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Setup chat input and send button
function setupChatInput() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    
    // Send message on button click
    sendButton.addEventListener('click', () => {
        sendMessage();
    });
    
    // Send message on Enter key
    messageInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
}

// Send a message
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const messageText = messageInput.value.trim();
    
    if (!messageText) return;
    
    let data;
    if (currentContact) {
        data = {
            message: messageText,
            receiver_id: currentContact
        };
    } else if (currentGroup) {
        data = {
            message: messageText,
            group_id: currentGroup
        };
    } else {
        return; // No chat selected
    }
    
    fetch('/api/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear input
            messageInput.value = '';
            
            // Append new message
            const messagesContainer = document.getElementById('messages');
            const messageElement = document.createElement('div');
            messageElement.className = 'message own';
            messageElement.setAttribute('data-id', data.message.id);
            
            messageElement.innerHTML = `
                <div class="message-content">
                    <div class="message-text">${data.message.message}</div>
                    <div class="message-time">${formatTime(data.message.timestamp)}</div>
                </div>
            `;
            
            // Add click event for message actions
            messageElement.addEventListener('click', () => {
                showMessageActions(data.message.id);
            });
            
            messagesContainer.appendChild(messageElement);
            
            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    })
    .catch(error => {
        // Error handling for sending messages
    });
}

// Show message actions (edit/delete)
function showMessageActions(messageId) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Message Options</h3>
                <span class="close">&times;</span>
            </div>
            <div class="modal-body">
                <button id="edit-message-btn">Edit Message</button>
                <button id="delete-message-btn">Delete Message</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal
    modal.style.display = 'block';
    
    // Handle close button
    modal.querySelector('.close').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Handle edit button
    modal.querySelector('#edit-message-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
        showEditMessageModal(messageId);
    });
    
    // Handle delete button
    modal.querySelector('#delete-message-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
        showDeleteMessageConfirmation(messageId);
    });
}

// Show edit message modal
function showEditMessageModal(messageId) {
    const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
    const messageText = messageElement.querySelector('.message-text').textContent;
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Edit Message</h3>
                <span class="close">&times;</span>
            </div>
            <div class="modal-body">
                <textarea id="edit-message-text">${messageText}</textarea>
                <button id="save-edit-btn">Save</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal and focus textarea
    modal.style.display = 'block';
    const textarea = modal.querySelector('#edit-message-text');
    textarea.focus();
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    
    // Handle close button
    modal.querySelector('.close').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Handle save button
    modal.querySelector('#save-edit-btn').addEventListener('click', () => {
        const newText = textarea.value.trim();
        if (newText && newText !== messageText) {
            fetch(`/api/messages/${messageId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: newText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update message in UI
                    messageElement.querySelector('.message-text').textContent = newText;
                    // Add edited label if not present
                    if (!messageElement.querySelector('.edited-label')) {
                        const timeElement = messageElement.querySelector('.message-time');
                        const editedLabel = document.createElement('span');
                        editedLabel.className = 'edited-label';
                        editedLabel.textContent = ' (edited)';
                        timeElement.after(editedLabel);
                    }
                }
            })
            .catch(error => {
                // Error handling for updating messages
            });
        }
        document.body.removeChild(modal);
    });
}

// Show delete message confirmation
function showDeleteMessageConfirmation(messageId) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Delete Message</h3>
                <span class="close">&times;</span>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete this message?</p>
                <button id="confirm-delete-btn">Delete</button>
                <button id="cancel-delete-btn">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show modal
    modal.style.display = 'block';
    
    // Handle close button
    modal.querySelector('.close').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Handle cancel button
    modal.querySelector('#cancel-delete-btn').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Handle confirm button
    modal.querySelector('#confirm-delete-btn').addEventListener('click', () => {
        fetch(`/api/messages/${messageId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove message from UI
                const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
                messageElement.remove();
            }
        })
        .catch(error => {
            // Error handling for deleting messages
        });
        
        document.body.removeChild(modal);
    });
}

// Setup message actions (edit/delete on click)
function setupMessageActions() {
    // This is handled in the displayMessages function
    // where we add click event handlers to each message
} 