// WebSocket Messenger - Socket.IO Client

// Initialize Socket.IO connection
const socket = io();

// State management
let currentChat = null;
let currentChatType = null; // 'user' or 'group'
let users = [];
let groups = [];
// Unread counts: key = 'user_email' or 'group_id'
const unreadCounts = {};
let currentUserEmail = null;

// DOM Elements
const userList = document.getElementById('userList');
const groupList = document.getElementById('groupList');
const messages = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatHeader = document.getElementById('chatHeader');
const createGroupBtn = document.getElementById('createGroupBtn');
const createGroupModal = document.getElementById('createGroupModal');
const cancelGroupBtn = document.getElementById('cancelGroupBtn');
const confirmGroupBtn = document.getElementById('confirmGroupBtn');
const groupMembersList = document.getElementById('groupMembersList');
const groupNameInput = document.getElementById('groupName');

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;

        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Show corresponding content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        document.getElementById(`${tab}-tab`).classList.remove('hidden');
    });
});

// Load users and groups on page load
window.addEventListener('DOMContentLoaded', () => {
    // Get current user email
    const container = document.querySelector('.chat-container');
    if (container) {
        currentUserEmail = container.dataset.currentUserEmail;
    }

    loadUsers();
    loadGroups();
});

// Socket.IO event listeners
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('receive_private_message', (data) => {
    const isChatOpen = currentChatType === 'user' && (currentChat === data.sender_email || currentChat === data.receiver_email);

    // Show message if we're chatting with either the sender or receiver
    if (isChatOpen) {
        const displayName = data.is_own ? 'You' : data.username;
        appendMessage(displayName, data.message, data.timestamp, data.is_own);
        scrollToBottom();
    }

    // Handle unread count
    // If I am NOT the sender, and (chat is not open OR window is not focused - assuming simple focus for now)
    if (!data.is_own && !(currentChatType === 'user' && currentChat === data.sender_email)) {
        const key = `user_${data.sender_email}`;
        unreadCounts[key] = (unreadCounts[key] || 0) + 1;
        renderUsers();
        updateTabBadges();

        // Optional: Play sound or notification title
    }
});

socket.on('receive_group_message', (data) => {
    if (currentChatType === 'group' && currentChat === data.group_id) {
        const isOwn = data.sender_email === currentUserEmail;
        appendMessage(data.username, data.message, data.timestamp, isOwn);
        scrollToBottom();
    } else {
        // If I am NOT the sender
        if (data.sender_email !== currentUserEmail) {
            const key = `group_${data.group_id}`;
            unreadCounts[key] = (unreadCounts[key] || 0) + 1;
            renderGroups();
            updateTabBadges();
        }
    }
});

socket.on('group_created', (data) => {
    loadGroups();
    // Only show alert to the creator
    if (data.is_creator) {
        alert(`Group "${data.group_name}" created successfully!`);
    }
});

socket.on('group_left', (data) => {
    loadGroups();
    if (currentChatType === 'group' && currentChat === data.group_id) {
        clearChat();
    }
});

socket.on('error', (data) => {
    alert('Error: ' + data.message);
});

socket.on('user_online', (data) => {
    // Update user's online status
    const user = users.find(u => u.email === data.email);
    if (user) {
        user.is_online = true;
        renderUsers();
    }
});

socket.on('user_offline', (data) => {
    // Update user's online status
    const user = users.find(u => u.email === data.email);
    if (user) {
        user.is_online = false;
        renderUsers();
    }
});

// Load users from API
async function loadUsers() {
    try {
        const response = await fetch('/api/chat/users');
        users = await response.json();
        renderUsers();
    } catch (error) {
        console.error('Error loading users:', error);
        userList.innerHTML = '<p class="error">Failed to load users</p>';
    }
}

// Load groups from API
async function loadGroups() {
    try {
        const response = await fetch('/api/chat/groups');
        groups = await response.json();
        renderGroups();
    } catch (error) {
        console.error('Error loading groups:', error);
        groupList.innerHTML = '<p class="error">Failed to load groups</p>';
    }
}

// Render users list
function renderUsers() {
    if (users.length === 0) {
        userList.innerHTML = '<p class="empty-state">No users available</p>';
        return;
    }

    userList.innerHTML = users.map(user => {
        const unread = unreadCounts[`user_${user.email}`] || 0;
        return `
        <div class="user-item" data-email="${user.email}">
            ${user.is_online ? '<div class="online-status"></div>' : '<div style="width: 10px;"></div>'}
            <div class="user-info">
                <div>${user.username}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">${user.email}</div>
            </div>
            ${unread > 0 ? `<div class="unread-badge">${unread}</div>` : ''}
        </div>
    `}).join('');

    // Add click listeners
    document.querySelectorAll('.user-item').forEach(item => {
        item.addEventListener('click', () => {
            const email = item.dataset.email;
            openPrivateChat(email);
        });
    });
}

// Render groups list
function renderGroups() {
    if (groups.length === 0) {
        groupList.innerHTML = '<p class="empty-state">No groups yet</p>';
        return;
    }

    groupList.innerHTML = groups.map(group => {
        const unread = unreadCounts[`group_${group.id}`] || 0;
        return `
        <div class="group-item ${group.has_left ? 'left' : ''}" data-id="${group.id}">
            <div style="flex: 1">
                <div>${group.name}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">
                    ${group.has_left ? 'Left' : `${group.active_member_count} members`}
                </div>
            </div>
            ${unread > 0 && !group.has_left ? `<div class="unread-badge">${unread}</div>` : ''}
            
            ${group.has_left ? `
                <button class="btn btn-secondary" onclick="deleteGroupData(${group.id})" 
                        style="margin-top: 8px; font-size: 11px; padding: 4px 8px;">
                    Delete
                </button>
            ` : `
                <button class="btn btn-secondary" onclick="leaveGroup(${group.id})" 
                        style="margin-top: 8px; font-size: 11px; padding: 4px 8px;">
                    Leave
                </button>
            `}
        </div>
    `}).join('');

    // Add click listeners
    document.querySelectorAll('.group-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') return;
            const groupId = parseInt(item.dataset.id);
            openGroupChat(groupId);
        });
    });
}

// Open private chat
async function openPrivateChat(email) {
    currentChat = email;
    currentChatType = 'user';

    // Clear unread count
    if (unreadCounts[`user_${email}`]) {
        delete unreadCounts[`user_${email}`];
        renderUsers();
        updateTabBadges();
    }

    // Update UI
    document.querySelectorAll('.user-item, .group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.user-item[data-email="${email}"]`).classList.add('active');

    const user = users.find(u => u.email === email);
    chatHeader.innerHTML = `<h3>Chat with ${user.username}</h3>`;

    // Load message history
    await loadPrivateHistory(email);

    // Enable input
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.focus();
}

// Open group chat
async function openGroupChat(groupId) {
    currentChat = groupId;
    currentChatType = 'group';

    // Clear unread count
    if (unreadCounts[`group_${groupId}`]) {
        delete unreadCounts[`group_${groupId}`];
        renderGroups();
        updateTabBadges();
    }

    // Update UI
    document.querySelectorAll('.user-item, .group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.group-item[data-id="${groupId}"]`).classList.add('active');

    const group = groups.find(g => g.id === groupId);
    chatHeader.innerHTML = `<h3>${group.name}</h3>`;

    // Load message history
    await loadGroupHistory(groupId);

    // Enable input only if not left
    if (!group.has_left) {
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();

        // Join the channel
        socket.emit('join_channel', { group_id: groupId });
    } else {
        messageInput.disabled = true;
        sendBtn.disabled = true;
    }
}

// Load private message history
async function loadPrivateHistory(email) {
    try {
        const response = await fetch(`/api/chat/history/private/${encodeURIComponent(email)}`);
        const history = await response.json();

        messages.innerHTML = '';
        if (history.length === 0) {
            messages.innerHTML = '<p class="empty-state">No messages yet. Start a conversation!</p>';
        } else {
            history.forEach(msg => {
                appendMessage(msg.username, msg.content, msg.timestamp, msg.is_own);
            });
        }
        scrollToBottom();
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Load group message history
async function loadGroupHistory(groupId) {
    try {
        const response = await fetch(`/api/chat/history/group/${groupId}`);
        const history = await response.json();

        messages.innerHTML = '';
        if (history.length === 0) {
            messages.innerHTML = '<p class="empty-state">No messages yet. Start a conversation!</p>';
        } else {
            history.forEach(msg => {
                appendMessage(msg.username, msg.content, msg.timestamp, msg.is_own);
            });
        }
        scrollToBottom();
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Send message
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !currentChat) return;

    if (currentChatType === 'user') {
        socket.emit('send_private_message', {
            receiver_email: currentChat,
            message: message
        });
    } else if (currentChatType === 'group') {
        socket.emit('send_group_message', {
            group_id: currentChat,
            message: message
        });
    }

    // Don't append immediately - wait for server confirmation to avoid duplicates
    messageInput.value = '';
}

// Append message to chat
function appendMessage(username, content, timestamp, isOwn) {
    if (messages.querySelector('.empty-state')) {
        messages.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOwn ? 'own' : ''}`;

    const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message-sender">${username}</div>
        <div class="message-content">${escapeHtml(content)}</div>
        <div class="message-time">${time}</div>
    `;

    messages.appendChild(messageDiv);
}

// Scroll to bottom of messages
function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
}

// Clear chat
function clearChat() {
    currentChat = null;
    currentChatType = null;
    messages.innerHTML = '<p class="empty-state">No messages yet. Start a conversation!</p>';
    chatHeader.innerHTML = '<h3>Select a user or group to start chatting</h3>';
    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.value = '';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Create group modal
createGroupBtn.addEventListener('click', () => {
    createGroupModal.classList.remove('hidden');
    loadUsersForGroup();
});

cancelGroupBtn.addEventListener('click', () => {
    createGroupModal.classList.add('hidden');
    groupNameInput.value = '';
});

confirmGroupBtn.addEventListener('click', () => {
    const groupName = groupNameInput.value.trim();
    const selectedUsers = Array.from(document.querySelectorAll('.checkbox-item input:checked'))
        .map(cb => cb.value);

    if (!groupName) {
        alert('Please enter a group name');
        return;
    }

    if (selectedUsers.length === 0) {
        alert('Please select at least one member');
        return;
    }

    socket.emit('create_group', {
        group_name: groupName,
        user_emails: selectedUsers
    });

    createGroupModal.classList.add('hidden');
    groupNameInput.value = '';
});

// Load users for group creation
function loadUsersForGroup() {
    if (users.length === 0) {
        groupMembersList.innerHTML = '<p class="loading">No users available</p>';
        return;
    }

    groupMembersList.innerHTML = users.map(user => `
        <div class="checkbox-item">
            <input type="checkbox" id="user-${user.email}" value="${user.email}">
            <label for="user-${user.email}">${user.username} (${user.email})</label>
        </div>
    `).join('');
}

// Leave group
function leaveGroup(groupId) {
    if (confirm('Are you sure you want to leave this group?')) {
        socket.emit('leave_group', { group_id: groupId });
    }
}

// Delete group data
function deleteGroupData(groupId) {
    if (confirm('Are you sure you want to delete this group data? This cannot be undone.')) {
        socket.emit('delete_group_data', { group_id: groupId });
        loadGroups();
    }
}

// Handle logout
const logoutForm = document.getElementById('logoutForm');
if (logoutForm) {
    logoutForm.addEventListener('submit', (e) => {
        e.preventDefault();
        // Emit logout signal to mark offline immediately
        socket.emit('logout_user');

        // Brief delay to ensure packet sends, then submit
        setTimeout(() => {
            logoutForm.submit();
        }, 100);
    });
}

// Update tab badges
function updateTabBadges() {
    let usersCount = 0;
    let groupsCount = 0;

    for (const key in unreadCounts) {
        if (unreadCounts[key] > 0) {
            if (key.startsWith('user_')) {
                usersCount++;
            } else if (key.startsWith('group_')) {
                groupsCount++;
            }
        }
    }

    const updateBadge = (id, count) => {
        const badge = document.getElementById(id);
        if (badge) {
            badge.textContent = count;
            if (count > 0) {
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    };

    updateBadge('usersTabBadge', usersCount);
    updateBadge('groupsTabBadge', groupsCount);
}
