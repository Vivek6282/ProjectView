/* ============================================================
   Project View — Chat Engine
   AJAX polling, @mentions, file upload, auto-scroll
   ============================================================ */

const ChatApp = {
    // --- State Properties: These keep track of what the user is currently doing ---
    currentRoomId: null,      // Stores the ID of the chat room the user has currently opened
    pollTimer: null,         // Holds the interval timer that checks for new messages every few seconds
    roomPollTimer: null,     // Holds the interval timer that updates the sidebar room list
    lastMessageId: 0,        // Keeps track of the latest message ID received to avoid re-fetching old messages
    selectedFile: null,      // Stores any file the user has picked to upload but hasn't sent yet
    mentionActive: false,    // A flag to know if the "@mention" popup is currently showing on screen
    mentionQuery: '',        // The text typed after the "@" symbol (used for searching users)
    mentionStartPos: 0,      // The cursor position where the "@" was typed (so we know where to insert the name)
    mentionIndex: 0,         // Which user is currently highlighted in the mention suggestion list
    mentionUsers: [],        // The list of users returned from the server for the current mention search
    currentMembers: [],      // The list of people who belong to the current chat room
    lastDateLabel: '',       // Stores the last date divider shown (e.g., "Today") to avoid duplicates
    isInit: false,           // Prevents the chat app from initializing multiple times

    // --- Initialize the Chat Application ---
    init() {
        // If already started, don't start again (Safety check)
        if (this.isInit) return;

        // Check if the server-side configuration is available (CSRF tokens, API URLs, etc.)
        if (typeof CHAT_CONFIG === 'undefined') {
            console.error('ChatApp: CHAT_CONFIG missing');
            return;
        }

        // Store the config for easy access throughout the app
        this.config = CHAT_CONFIG;
        // Grab important UI elements from the HTML page
        this.textarea = document.getElementById('chatInput');      // The typing area
        this.messagesEl = document.getElementById('chatMessages'); // The scrolling message container
        this.mentionPopup = document.getElementById('mentionPopup'); // The floating @member list
        this.sendBtn = document.getElementById('chatSendBtn');     // The "Send" button

        // If the typing area exists, set up its interactive features
        if (this.textarea) {
            // Listen for every character typed (to handle mentions and resizing)
            this.textarea.addEventListener('input', () => this.onInput());
            // Listen for special keys like "Enter" to send the message
            this.textarea.addEventListener('keydown', (e) => this.onKeyDown(e));
            
            // UI/UX: Auto-growing textarea. The box gets taller as you type more lines.
            this.textarea.addEventListener('input', () => {
                this.textarea.style.height = 'auto'; // Reset height to recalculate
                // Set height based on content, but cap it at 120px to save screen space
                this.textarea.style.height = Math.min(this.textarea.scrollHeight, 120) + 'px';
            });
        }

        // If the send button exists, set up the click action
        if (this.sendBtn) {
            this.sendBtn.onclick = null; // Clean up any old click events
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Feature: Room Search. Allows users to filter the sidebar by typing a name.
        const searchInput = document.getElementById('roomSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterRooms(e.target.value));
        }

        // Backend Sync: Update the sidebar list every 10 seconds to show new rooms or unread counts
        this.roomPollTimer = setInterval(() => this.pollRooms(), 10000);

        // Feature: Deep Linking. If the URL has "?room=5", automatically open room #5 on load.
        const urlParams = new URLSearchParams(window.location.search);
        const roomId = urlParams.get('room');
        if (roomId) {
            setTimeout(() => this.loadRoom(parseInt(roomId)), 100);
        }

        // Mark as successfully initialized
        this.isInit = true;
    },

    /* ----------------------------------------------------------------
       Room Management
    ---------------------------------------------------------------- */

    // --- Load Room: Fetches all messages and data for a specific chat ---
    loadRoom(roomId) {
        // UI/UX: Stop polling the previous room before switching to the new one
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }

        // Update state to current selection
        this.currentRoomId = roomId;
        this.lastMessageId = 0; // Reset so we fetch everything from scratch for this room
        this.lastDateLabel = ''; // Reset date dividers

        // UI Effect: Highlight the selected room in the sidebar (add 'active' class)
        document.querySelectorAll('.pv-chat-room-item').forEach(el => {
            el.classList.toggle('active', parseInt(el.dataset.roomId) === roomId);
        });

        // UI Toggle: Switch from the "Select a chat" placeholder to the actual chat interface
        const placeholder = document.getElementById('chatPlaceholder');
        const active = document.getElementById('chatActive');
        if (placeholder) placeholder.style.display = 'none';
        if (active) active.style.display = 'flex';

        // Responsive Design: On mobile, slide the chat panel into view
        const container = document.querySelector('.pv-chat-container');
        if (container) container.classList.add('room-open');

        // UI Clean: Clear out messages from the previous room
        if (this.messagesEl) this.messagesEl.innerHTML = '';

        // Backend API Call: Fetch room info and message history
        fetch(`${this.config.apiBase}${roomId}/messages/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            // Store the member list for @mentions
            this.currentMembers = data.members || [];
            // UI Update: Set the top bar title, avatar, and participant count
            this.renderHeader(data);
            // UI Update: Place all fetched messages into the chat area
            this.renderAllMessages(data.messages);

            // UI UX: Clean up the sidebar by removing unread notifications for this room
            const roomEl = document.querySelector(`.pv-chat-room-item[data-room-id="${roomId}"]`);
            if (roomEl) {
                roomEl.classList.remove('has-unread');
                const badge = roomEl.querySelector('.pv-chat-unread-badge');
                if (badge) badge.remove();
            }

            // Real-time Feature: Start checking for new incoming messages every 3 seconds
            this.pollTimer = setInterval(() => this.pollMessages(), 3000);
        })
        .catch(err => console.error('Failed to load room:', err));
    },

    // --- Close Room: Handles the UI when exiting a chat (especially on mobile) ---
    closeRoom() {
        const container = document.querySelector('.pv-chat-container');
        // Mobile UI: Slide the chat panel back out of view
        if (container) container.classList.remove('room-open');

        // Clear current state
        this.currentRoomId = null;
        // Optimization: Stop the timer that checks for messages since no chat is open
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    },

    // --- Toggle Sidebar: Collapses or expands the room list for a cleaner view ---
    toggleSidebar() {
        const container = document.querySelector('.pv-chat-container');
        if (container) container.classList.toggle('sidebar-collapsed');
    },

    filterRooms(query) {
        const q = query.toLowerCase().trim();
        document.querySelectorAll('.pv-chat-room-item').forEach(el => {
            const name = el.querySelector('.pv-chat-room-name');
            if (!name) return;
            const match = name.textContent.toLowerCase().includes(q);
            el.style.display = match ? '' : 'none';
        });
    },

    /* ----------------------------------------------------------------
       Render
    ---------------------------------------------------------------- */

    // --- Render Header: Updates the top bar of the chat area ---
    renderHeader(data) {
        const avatar = document.getElementById('chatHeaderAvatar'); // Circle with the initial
        const name = document.getElementById('chatHeaderName');     // Room name text
        const members = document.getElementById('chatHeaderMembers'); // Participant count text

        this.currentRoomData = data; // Save the full data object for use in the "Info" panel later

        // UI Detail: Create a colorful avatar based on the group name
        if (avatar) {
            const roomName = data.room_name || 'Chat';
            avatar.textContent = roomName[0].toUpperCase(); // First letter of the name
            avatar.style.backgroundColor = this.getAvatarColor(roomName); // Unique color for this name
            avatar.style.color = '#fff'; // White text for contrast
            avatar.style.display = 'flex'; // Layout centering
            avatar.style.alignItems = 'center';
            avatar.style.justifyContent = 'center';
        }
        // UI UX: Update the visible name in the header
        if (name) name.textContent = data.room_name;
        // UI UX: Show how many people are in the conversation
        if (members) {
            const count = (data.members || []).length;
            members.textContent = `${count} participants`;
        }
    },

    // --- Toggle Info: Opens or closes the right-side details panel ---
    toggleInfo() {
        const container = document.querySelector('.pv-chat-container');
        if (!container) return;

        // UI Effect: Toggle the CSS class that slides the info panel in/out
        const isOpen = container.classList.toggle('info-open');
        // If opening, populate it with the current room's details
        if (isOpen && this.currentRoomData) {
            this.renderRoomInfo(this.currentRoomData);
        }
    },

    // --- Render Room Info: Populates the details sidebar (Member list, Delete button) ---
    renderRoomInfo(data) {
        const avatar = document.getElementById('chatInfoAvatarFull');
        const name = document.getElementById('chatInfoNameFull');
        const type = document.getElementById('chatInfoTypeFull');
        const list = document.getElementById('chatInfoMemberListFull');
        const body = document.querySelector('.pv-chat-info-body');
        const headerTitle = document.querySelector('.pv-chat-info-header span');

        // Logic: Check if this is a 1-on-1 chat or a group
        const isDirect = data.room_type === 'DIRECT';
        const members = data.members || [];

        // UI UX: Set the sidebar title dynamically
        if (headerTitle) {
            headerTitle.textContent = isDirect ? 'Contact Info' : 'Group Info';
        }

        // UI Detail: Large avatar in the info panel
        if (avatar) {
            const roomName = data.room_name || 'Chat';
            avatar.textContent = roomName[0].toUpperCase();
            avatar.style.background = this.getAvatarColor(roomName);
        }
        if (name) name.textContent = data.room_name || 'Info';
        if (type) {
            type.textContent = isDirect ? 'Personal Chat' : `${members.length} Participants`;
        }
        
        // UI UX: Generate the HTML list of members with their roles and avatars
        if (list) {
            list.innerHTML = members.map(m => {
                const color = this.getAvatarColor(m.username || 'User');
                const isMe = m.id === this.config.currentUserId;
                const roleBadge = m.is_staff ? '<span class="pv-mention-badge">Admin</span>' : '';
                
                return `
                    <div class="pv-info-member-item">
                        <div class="pv-info-member-avatar" style="background:${color}; color:#fff;">
                            ${(m.username || '?')[0].toUpperCase()}
                        </div>
                        <div class="pv-info-member-info">
                            <div class="fw-bold">
                                ${this.escapeHtml(m.username || 'User')} 
                                ${isMe ? '<small class="text-muted-custom ms-1">(You)</small>' : ''}
                                ${roleBadge}
                            </div>
                            <div class="smaller text-muted-custom">Hey there! I am using Project View.</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Feature: Security & Admin Tools. Add the "Delete Group" button only for authorized users.
        const existingActions = document.getElementById('chatInfoActions');
        if (existingActions) existingActions.remove(); // Clean up old buttons
        const isCreator = data.created_by_id === this.config.currentUserId;
        const isAdmin = this.config.userRole === 'manager' || this.config.userRole === 'hr';
        
        // UI Logic: Allow admins to delete ANY conversation, or creator to delete their own group
        const canDelete = isAdmin || (!isDirect && isCreator);

        if (canDelete) {
            const actionSection = document.createElement('div');
            actionSection.id = 'chatInfoActions';
            actionSection.className = 'pv-info-section mt-4 pt-3 border-top';
            actionSection.innerHTML = `
                <div class="px-4">
                    <button class="btn btn-danger w-100 py-2 fw-bold pv-btn-delete-group" onclick="ChatApp.deleteRoom(${data.room_id})">
                        <i class="bi bi-trash3 me-2"></i>Delete Group
                    </button>
                    <p class="smaller text-muted-custom text-center mt-2 mb-0">This action will permanently delete the group for all members.</p>
                </div>
            `;
            body.appendChild(actionSection);
        }
    },

    // --- Delete Room: Permanently removes a group chat ---
    deleteRoom(roomId) {
        // UI/UX: As requested, we removed the confirmation alert for "instant" deletion effect.
        // This makes the admin experience feel faster and more powerful.
        
        // Backend API Call: Completely remove the room from the database
        fetch(`${this.config.apiBase}${roomId}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': this.config.csrfToken } // Security: Include CSRF token for protection
        })
        .then(r => r.json())
        .then(data => {
            // If the server says "ok", refresh the page to update the UI
            if (data.status === 'ok') {
                window.location.reload();
            } else {
                // If there's an error (e.g., unauthorized), log it to the console
                console.error(data.error || 'Failed to delete room');
            }
        })
        .catch(err => {
            // Log any network errors
            console.error('Delete failed:', err);
        });
    },

    // --- Render All Messages: Wipes the screen and draws every message in the list ---
    renderAllMessages(messages) {
        if (!this.messagesEl) return;
        this.lastDateLabel = ''; // Reset date tracking so today's first message gets a date header
        messages.forEach(msg => this.appendMessage(msg));
        this.scrollToBottom(); // UI UX: Jump to the most recent message
    },

    // --- Append Message: Adds a single message bubble to the bottom of the chat ---
    appendMessage(msg) {
        if (!this.messagesEl) return;

        // --- Step 1: Update the latest ID so we don't fetch this message again ---
        if (msg.id > this.lastMessageId) this.lastMessageId = msg.id;

        // --- Step 2: Date Dividers ---
        // UIUX: If the message is from a new day, add a "Today" or "Yesterday" separator
        const msgDate = new Date(msg.created_at);
        const dateLabel = this.getDateLabel(msgDate);
        if (dateLabel !== this.lastDateLabel) {
            this.lastDateLabel = dateLabel;
            const divider = document.createElement('div');
            divider.className = 'pv-chat-date-divider';
            divider.innerHTML = `<span class="pv-chat-date-label">${dateLabel}</span>`;
            this.messagesEl.appendChild(divider);
        }

        // --- Step 3: Parse Message Properties ---
        const isOwn = msg.is_own; // Was it sent by the current user?
        const isMentioned = msg.is_mentioned; // Does it contain @[MyName]?
        const isEdited = msg.created_at !== msg.updated_at; // Was the text changed after sending?
        const content = msg.content || '';
        const isForwarded = content.includes('*[Forwarded]*'); // Was it sent from another group?
        const cleanContent = content.replace('*[Forwarded]*\n', ''); // Strip the technical tag for display

        // --- Step 4: Create the Message Container ---
        const wrapper = document.createElement('div');
        // UI: Apply different classes for own messages (right side) vs others (left side)
        wrapper.className = `pv-msg-wrapper ${isOwn ? 'own' : 'other'} ${isMentioned ? 'mentioned' : ''}`;
        wrapper.dataset.msgId = msg.id;

        // --- Step 5: Build the Avatar (for other people's messages) ---
        let avatarHtml = '';
        if (!isOwn) {
            const color = this.getAvatarColor(msg.sender_username);
            avatarHtml = `<div class="pv-chat-avatar-sm" style="background:${color};color:#fff;">${msg.sender_username[0].toUpperCase()}</div>`;
        }

        // --- Step 6: Render Text Content ---
        // Security/UX: Convert mentions and links into clickable HTML safely
        const contentHtml = this.renderContent(cleanContent, isOwn);

        // --- Step 7: Handle Attachments (Images/Files) ---
        let attachHtml = '';
        if (msg.attachment_url) {
            if (msg.is_image) {
                // UI: Show a clickable image preview
                attachHtml = `<div class="pv-msg-attachment"><img src="${msg.attachment_url}" alt="${msg.attachment_name}" onclick="window.open('${msg.attachment_url}','_blank')" loading="lazy"></div>`;
            } else {
                // UI: Show a file download link with an icon
                attachHtml = `<div class="pv-msg-attachment"><a href="${msg.attachment_url}" target="_blank" class="pv-msg-file-link"><i class="bi bi-file-earmark-arrow-down"></i>${this.escapeHtml(msg.attachment_name)}</a></div>`;
            }
        }

        // Time
        // --- Step 8: Calculate Display Time ---
        const time = msgDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // --- Step 9: Sender Label ---
        // UI UX: Show the username and "admin" badge for other people
        const senderLine = !isOwn
            ? `<div class="pv-msg-sender">${this.escapeHtml(msg.sender_username)}${msg.sender_is_staff ? ' <span style="opacity:0.6">• admin</span>' : ''}</div>`
            : '';

        // --- Step 10: Assemble the final HTML Bubble ---
        const editedAt = msg.edited_at ? new Date(msg.edited_at).getTime() : 0;
        const showEdited = msg.is_edited && (Date.now() - editedAt < 300000);

        wrapper.innerHTML = `
            ${avatarHtml}
            <div class="pv-msg-bubble">
                <div class="pv-msg-trigger" onclick="ChatApp.openContextMenu(event, ${msg.id}, ${isOwn})">
                    <i class="bi bi-chevron-down"></i>
                </div>
                ${isForwarded ? '<span class="pv-msg-forwarded"><i class="bi bi-arrow-90deg-right me-1"></i>Forwarded</span>' : ''}
                ${senderLine}
                <div class="pv-msg-content">${contentHtml}</div>
                ${attachHtml}
                <div class="pv-msg-time">
                    ${time}
                    <span class="pv-msg-edited" data-edited-at="${editedAt}" style="display: ${showEdited ? 'inline' : 'none'}">(edited)</span>
                </div>
            </div>
        `;

        // Feature: Mobile Long Press. Opens the menu when holding down on a message.
        this.bindLongPress(wrapper, msg.id, isOwn);

        // Final Touch: Add it to the screen
        this.messagesEl.appendChild(wrapper);
    },

    /* ----------------------------------------------------------------
       Context Menu & Long Press
    ---------------------------------------------------------------- */

    // --- Bind Long Press: Enables mobile-friendly interaction ---
    bindLongPress(el, msgId, isOwn) {
        let pressTimer;
        // Effect: When the user starts touching the message
        const handleStart = () => {
            // Set a timer for 700ms. If they hold that long, open the menu.
            pressTimer = setTimeout(() => {
                el.classList.add('is-pressing'); // UI Visual feedback
                this.openContextMenu(null, msgId, isOwn, el);
            }, 700);
        };
        // Effect: If they let go early, cancel the timer
        const handleEnd = () => {
            clearTimeout(pressTimer);
            el.classList.add('is-pressing');
            setTimeout(() => el.classList.remove('is-pressing'), 100);
        };

        el.addEventListener('touchstart', handleStart);
        el.addEventListener('touchend', handleEnd);
    },

    // --- Open Context Menu: Shows Forward/Edit/Delete options ---
    openContextMenu(e, msgId, isOwn, el) {
        // UI UX: Prevent the browser's default right-click menu
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Clean: Close any existing menu first
        this.closeContextMenu();

        // UI UX: Create a floating menu element
        const menu = document.createElement('div');
        menu.className = 'pv-chat-context-menu';
        
        // Feature: Define what actions are available
        let actions = `
            <div class="pv-context-item" onclick="ChatApp.startForward(${msgId})">
                <i class="bi bi-arrow-90deg-right"></i> Forward
            </div>
        `;

        // If it's the user's own message, they can edit or delete it
        if (isOwn) {
            actions += `
                <div class="pv-context-item" onclick="ChatApp.startEdit(${msgId})">
                    <i class="bi bi-pencil"></i> Edit
                </div>
                <div class="pv-context-item text-danger" onclick="ChatApp.deleteMessage(${msgId})">
                    <i class="bi bi-trash"></i> Delete
                </div>
            `;
        }

        menu.innerHTML = actions;
        document.body.appendChild(menu);

        // UI UX: Position the menu exactly where the user clicked or touched
        const x = e ? e.clientX : el.getBoundingClientRect().left + 20;
        const y = e ? e.clientY : el.getBoundingClientRect().top + 20;
        
        // Safety: Ensure the menu doesn't go off the screen edges
        const rect = menu.getBoundingClientRect();
        let finalX = x;
        let finalY = y;
        if (x + rect.width > window.innerWidth) finalX = window.innerWidth - rect.width - 10;
        if (y + rect.height > window.innerHeight) finalY = window.innerHeight - rect.height - 10;

        menu.style.left = `${finalX}px`;
        menu.style.top = `${finalY}px`;

        // UI UX: If the user clicks anywhere else, close the menu automatically
        setTimeout(() => {
            document.addEventListener('click', () => this.closeContextMenu(), { once: true });
        }, 100);
    },

    // --- Close Context Menu: Removes the menu from the DOM ---
    closeContextMenu() {
        const menu = document.querySelector('.pv-chat-context-menu');
        if (menu) menu.remove();
    },

    /* ----------------------------------------------------------------
       Actions: Edit, Delete, Forward
    ---------------------------------------------------------------- */

    // --- Start Edit: Replaces the message text with an input field ---
    startEdit(msgId) {
        this.closeContextMenu();
        // UI UX: Find the specific message bubble being edited
        const wrapper = document.querySelector(`.pv-msg-wrapper[data-msg-id="${msgId}"]`);
        const contentEl = wrapper.querySelector('.pv-msg-content');
        const text = contentEl.innerText;

        // UI UX: Hide the static text and show a textarea instead
        contentEl.style.display = 'none';
        const inputWrap = document.createElement('div');
        inputWrap.className = 'pv-msg-edit-wrap';
        inputWrap.innerHTML = `
            <textarea class="form-control pv-input p-2 mb-1" style="font-size:0.85rem;">${text}</textarea>
            <div class="d-flex gap-2">
                <button class="btn btn-sm pv-btn-primary px-2 py-0" onclick="ChatApp.saveEdit(${msgId})">Save</button>
                <button class="btn btn-sm btn-light border px-2 py-0" onclick="ChatApp.cancelEdit(${msgId})">Cancel</button>
            </div>
        `;
        contentEl.after(inputWrap);
        inputWrap.querySelector('textarea').focus(); // UI UX: Focus the box so you can type immediately
    },

    // --- Save Edit: Sends the updated text to the backend ---
    saveEdit(msgId) {
        const wrapper = document.querySelector(`.pv-msg-wrapper[data-msg-id="${msgId}"]`);
        const text = wrapper.querySelector('textarea').value.trim();
        if (!text) return; // Feature: Don't allow empty messages

        const formData = new FormData();
        formData.append('content', text);

        // Backend API Call: Update the message content in the database
        fetch(`${this.config.apiBase}/messages/${msgId}/edit/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(r => r.json())
        .then(data => {
            if (data.message) {
                // UI UX: Replace the textarea with the new updated text
                const contentEl = wrapper.querySelector('.pv-msg-content');
                contentEl.innerHTML = this.renderContent(data.message.content, true);
                const timeEl = wrapper.querySelector('.pv-msg-time');
                // UI Detail: Add the "(edited)" label if not already there
                if (!timeEl.querySelector('.pv-msg-edited')) {
                    timeEl.innerHTML += '<span class="pv-msg-edited">(edited)</span>';
                }
                this.cancelEdit(msgId); // Restore normal view
            }
        });
    },

    // --- Cancel Edit: Restores the original message view without saving ---
    cancelEdit(msgId) {
        const wrapper = document.querySelector(`.pv-msg-wrapper[data-msg-id="${msgId}"]`);
        const editWrap = wrapper.querySelector('.pv-msg-edit-wrap');
        const contentEl = wrapper.querySelector('.pv-msg-content');
        if (editWrap) editWrap.remove();
        contentEl.style.display = 'block';
    },

    // --- Delete Message: Removes a single message from the view and DB ---
    deleteMessage(msgId) {
        this.closeContextMenu();
        // UI UX: Confirm before deleting a specific message (Safety)
        if (!confirm('Are you sure you want to delete this message?')) return;

        // Backend API Call: Soft delete the message (hides it from others too)
        fetch(`${this.config.apiBase}/messages/${msgId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                // UI UX: Remove the message bubble from the screen instantly
                const wrapper = document.querySelector(`.pv-msg-wrapper[data-msg-id="${msgId}"]`);
                if (wrapper) wrapper.remove();
            }
        });
    },

    // --- Start Forward: Opens a list of rooms to send a message to ---
    startForward(msgId) {
        this.closeContextMenu();
        this.forwardingMsgId = msgId;
        
        // UI UX: Create a Bootstrap Modal popup for choosing where to forward
        const modalHtml = `
            <div class="modal fade" id="forwardModal" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered modal-sm">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header border-0 pb-0">
                            <h5 class="modal-title fs-6 fw-bold">Forward Message</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="list-group list-group-flush" id="forwardRoomList">
                                <div class="text-center p-3"><div class="spinner-border spinner-border-sm text-primary"></div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // UI Clean: Remove old modal if it exists, then add the new one
        let modalEl = document.getElementById('forwardModal');
        if (modalEl) modalEl.remove();
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('forwardModal'));
        modal.show();

        // Backend API Call: Fetch all available chat rooms for the list
        fetch(`${this.config.apiBase}/rooms/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            // UI UX: Fill the modal with clickable buttons for each room
            const list = document.getElementById('forwardRoomList');
            list.innerHTML = data.rooms.map(room => `
                <button class="list-group-item list-group-item-action border-0 py-3 d-flex align-items-center gap-3" onclick="ChatApp.sendForward(${room.id})">
                    <div class="pv-chat-avatar-sm" style="background:var(--pv-accent-bg); color:var(--pv-accent); font-size:0.7rem;">
                        ${(room.name || '?')[0].toUpperCase()}
                    </div>
                    <span class="fs-7 fw-medium">${this.escapeHtml(room.name)}</span>
                </button>
            `).join('');
        });
    },

    // --- Send Forward: Executes the forwarding of a message ---
    sendForward(roomId) {
        const formData = new FormData();
        formData.append('room_id', roomId);

        // Backend API Call: Copy the message to the new room
        fetch(`${this.config.apiBase}/messages/${this.forwardingMsgId}/forward/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                // UI UX: Close the popup
                const modal = bootstrap.Modal.getInstance(document.getElementById('forwardModal'));
                modal.hide();
                // UI UX: If the target room is the one we are currently looking at, add the message to the screen immediately
                if (roomId === this.currentRoomId) {
                    this.appendMessage(data.message);
                    this.scrollToBottom();
                }
            }
        });
    },

    renderContent(text, isOwn) {
        if (!text) return '';
        let escaped = this.escapeHtml(text);
        // Highlight @mentions
        escaped = escaped.replace(/@(\w+)/g, '<span class="pv-mention">@$1</span>');
        // Convert newlines to <br>
        escaped = escaped.replace(/\n/g, '<br>');
        return escaped;
    },

    /* ----------------------------------------------------------------
       Polling
    ---------------------------------------------------------------- */

    // --- Poll Messages: The heart of the real-time experience ---
    pollMessages() {
        // Feature: Only poll if we are actually in a room
        if (!this.currentRoomId) return;

        // Backend API Call: Get any new messages that arrived after our last local message
        fetch(`${this.config.apiBase}${this.currentRoomId}/messages/?last_id=${this.lastMessageId}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                // UI UX: Check if the user is currently looking at the bottom of the chat
                const wasAtBottom = this.isAtBottom();
                data.messages.forEach(msg => {
                    // Logic: Ensure we don't accidentally add the same message twice
                    if (!this.messagesEl.querySelector(`[data-msg-id="${msg.id}"]`)) {
                        this.appendMessage(msg);
                    }
                });
                // UI UX: If they were at the bottom, scroll down to show the new message
                if (wasAtBottom) this.scrollToBottom();
            }
        })
        .catch(() => {}); // Silent failure (it will just try again next time)

        // UI UX: Refresh existing (edited) tags based on current time
        this.refreshEditedTags();
    },

    refreshEditedTags() {
        const now = Date.now();
        document.querySelectorAll('.pv-msg-edited').forEach(el => {
            const editedAt = parseInt(el.dataset.editedAt);
            if (editedAt > 0) {
                const isFresh = (now - editedAt) < 300000;
                el.style.display = isFresh ? 'inline' : 'none';
            }
        });
    },

    // --- Poll Rooms: Updates the sidebar with new data every 10s ---
    pollRooms() {
        // Backend API Call: Get a list of all rooms and their unread counts
        fetch(`${this.config.apiBase}/rooms/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            if (!data.rooms) return;
            data.rooms.forEach(room => {
                // UI UX: Find the corresponding room item in the sidebar
                const el = document.querySelector(`.pv-chat-room-item[data-room-id="${room.id}"]`);
                if (!el) return;

                // Feature: Unread Badges. Show a number if there are new messages.
                const existingBadge = el.querySelector('.pv-chat-unread-badge');
                // Only show badge for rooms we are NOT currently looking at
                if (room.unread_count > 0 && room.id !== this.currentRoomId) {
                    el.classList.add('has-unread');
                    if (existingBadge) {
                        existingBadge.textContent = room.unread_count; // UI UX: Update the number
                    } else {
                        // Create a new badge if it didn't exist
                        const meta = el.querySelector('.pv-chat-room-meta');
                        if (meta) {
                            const badge = document.createElement('div');
                            badge.className = 'pv-chat-unread-badge';
                            badge.textContent = room.unread_count;
                            meta.appendChild(badge);
                        }
                    }
                } else {
                    // UI UX: Remove the badge if no unread messages
                    el.classList.remove('has-unread');
                    if (existingBadge) existingBadge.remove();
                }

                // UI UX: Update the "preview" text in the sidebar (the last message sent)
                const preview = el.querySelector('.pv-chat-room-preview');
                if (preview && room.last_message) {
                    const sender = room.last_message_sender;
                    preview.innerHTML = `<strong>${this.escapeHtml(sender)}:</strong> ${this.escapeHtml(room.last_message)}`;
                }
            });
        })
        .catch(() => {});
    },

    /* ----------------------------------------------------------------
       Send Message
    ---------------------------------------------------------------- */

    // --- Send Message: The main action for sending text and files ---
    sendMessage() {
        // Feature: Don't do anything if no room is open
        if (!this.currentRoomId) return;
        // Logic: Get the text and strip whitespace
        const content = this.textarea ? this.textarea.value.trim() : '';
        // Feature: Don't send empty messages unless there's a file attached
        if (!content && !this.selectedFile) return;

        // Backend Integration: Prepare the data to be sent (Multipart for files)
        const formData = new FormData();
        formData.append('content', content);
        if (this.selectedFile) {
            formData.append('attachment', this.selectedFile);
        }

        // UI UX: Disable the send button during the upload to prevent double-sending
        const sendBtn = document.getElementById('chatSendBtn');
        if (sendBtn) sendBtn.disabled = true;

        // Backend API Call: Update the read status so the badge disappears
        fetch(`${this.config.apiBase}${this.currentRoomId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        });

        // Backend API Call: Send the message to the server
        fetch(`${this.config.apiBase}${this.currentRoomId}/send/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.config.csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(r => r.json())
        .then(data => {
            if (data.message) {
                // UI UX: Add the new message to the screen instantly for a "fast" feel
                if (!this.messagesEl.querySelector(`[data-msg-id="${data.message.id}"]`)) {
                    this.appendMessage(data.message);
                }
                this.scrollToBottom();
            }
            // UI UX: Clear the input box and reset its height
            if (this.textarea) {
                this.textarea.value = '';
                this.textarea.style.height = 'auto';
            }
            // UI Clean: Remove the file preview
            this.clearFile();
            // UI UX: Re-enable the send button
            if (sendBtn) sendBtn.disabled = false;

            // UI UX: Update the room's preview in the sidebar so the user sees their own last message
            const roomEl = document.querySelector(`.pv-chat-room-item[data-room-id="${this.currentRoomId}"]`);
            if (roomEl) {
                const preview = roomEl.querySelector('.pv-chat-room-preview');
                if (preview) {
                    preview.innerHTML = `<strong>You:</strong> ${this.escapeHtml(content || '[attachment]').substring(0, 35)}`;
                }
            }
        })
        .catch(err => {
            console.error('Send failed:', err);
            if (sendBtn) sendBtn.disabled = false;
        });
    },

    /* ----------------------------------------------------------------
       File Handling
    ---------------------------------------------------------------- */

    // --- Handle File: Logic when a user picks a file to upload ---
    handleFile(input) {
        const file = input.files && input.files[0];
        if (!file) return;

        // Feature: Size limit. Don't allow files larger than 10MB to protect the server.
        if (file.size > 10 * 1024 * 1024) {
            console.warn('File is too large. Maximum size is 10MB.');
            input.value = '';
            return;
        }

        // State: Save the file so sendMessage can use it
        this.selectedFile = file;
        // UI UX: Show a small preview box with the filename
        const preview = document.getElementById('chatFilePreview');
        const nameEl = document.getElementById('chatFileName');
        if (preview) preview.style.display = 'block';
        if (nameEl) nameEl.textContent = file.name;
    },

    // --- Clear File: Cancels the file selection ---
    clearFile() {
        this.selectedFile = null;
        // UI UX: Hide the preview and reset the file input field
        const preview = document.getElementById('chatFilePreview');
        const input = document.getElementById('chatFileInput');
        if (preview) preview.style.display = 'none';
        if (input) input.value = '';
    },

    /* ----------------------------------------------------------------
       @Mention System
    ---------------------------------------------------------------- */

    // --- On Input: Fires every time the user types a character ---
    onInput() {
        if (!this.textarea) return;
        const val = this.textarea.value;
        const cursorPos = this.textarea.selectionStart;

        // Feature: @Mentions. Look at the text before the cursor to see if it ends with "@name"
        const textBeforeCursor = val.substring(0, cursorPos);
        const atMatch = textBeforeCursor.match(/@(\w*)$/);

        if (atMatch) {
            // UI UX: Show the mention suggestion popup
            this.mentionActive = true;
            this.mentionQuery = atMatch[1]; // The characters typed after @
            this.mentionStartPos = cursorPos - atMatch[0].length; // Remember where the @ was
            this.searchMentions(this.mentionQuery); // Backend API Call
        } else {
            // UI UX: Close the popup if no @ match
            this.closeMentionPopup();
        }
    },

    // --- Search Mentions: Asks the server for users matching the typed name ---
    searchMentions(query) {
        if (!this.currentRoomId) return;

        // Backend API Call: Filter users by name within the current room
        fetch(`${this.config.apiBase}/mentions/?q=${encodeURIComponent(query)}&room_id=${this.currentRoomId}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            this.mentionUsers = data.users || [];
            this.mentionIndex = 0; // Highlight the first user in the list
            this.renderMentionPopup(); // UI Update
        })
        .catch(() => this.closeMentionPopup());
    },

    // --- Render Mention Popup: Builds the HTML for the suggestion list ---
    renderMentionPopup() {
        // UI UX: If no users found, hide the popup
        if (!this.mentionPopup || this.mentionUsers.length === 0) {
            this.closeMentionPopup();
            return;
        }

        // UI UX: Generate clickable items for each user
        this.mentionPopup.innerHTML = this.mentionUsers.map((u, i) => {
            const color = this.getAvatarColor(u.username);
            return `
                <div class="pv-mention-item ${i === this.mentionIndex ? 'active' : ''}"
                     onclick="ChatApp.insertMention('${u.username}')">
                    <div class="pv-chat-avatar-sm" style="background:${color};color:#fff;">${u.username[0].toUpperCase()}</div>
                    <span class="pv-mention-username">${this.escapeHtml(u.username)}</span>
                    ${u.is_staff ? '<span class="pv-mention-badge">Admin</span>' : ''}
                </div>
            `;
        }).join('');

        // UI Effect: Make the popup visible
        this.mentionPopup.classList.add('show');
    },

    // --- Insert Mention: Completes the mention when a user is selected ---
    insertMention(username) {
        if (!this.textarea) return;
        const val = this.textarea.value;
        const before = val.substring(0, this.mentionStartPos);
        const after = val.substring(this.textarea.selectionStart);
        // UI UX: Swap the @query with the full @username
        this.textarea.value = before + '@' + username + ' ' + after;
        this.textarea.focus();
        // UI UX: Place the cursor after the inserted name
        const newPos = this.mentionStartPos + username.length + 2;
        this.textarea.setSelectionRange(newPos, newPos);
        this.closeMentionPopup();
    },

    // --- Close Mention Popup: Hides the suggestion list and resets state ---
    closeMentionPopup() {
        this.mentionActive = false;
        this.mentionUsers = [];
        if (this.mentionPopup) this.mentionPopup.classList.remove('show');
    },

    // --- On Key Down: Handles keyboard shortcuts (Enter to send, Arrows for mentions) ---
    onKeyDown(e) {
        // UI UX: Send message on "Enter" unless "Shift" is held (for new lines)
        if (e.key === 'Enter' && !e.shiftKey && !this.mentionActive) {
            e.preventDefault();
            this.sendMessage();
            return;
        }

        // UI UX: Navigation within the @mention suggestion list
        if (this.mentionActive && this.mentionUsers.length > 0) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                // Move highlight down
                this.mentionIndex = Math.min(this.mentionIndex + 1, this.mentionUsers.length - 1);
                this.renderMentionPopup();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                // Move highlight up
                this.mentionIndex = Math.max(this.mentionIndex - 1, 0);
                this.renderMentionPopup();
            } else if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                // Select the currently highlighted user
                if (this.mentionUsers[this.mentionIndex]) {
                    this.insertMention(this.mentionUsers[this.mentionIndex].username);
                }
            } else if (e.key === 'Escape') {
                // Feature: Close mentions without selecting anyone
                this.closeMentionPopup();
            }
        }
    },

    /* ----------------------------------------------------------------
       Utilities
    ---------------------------------------------------------------- */

    // --- Scroll To Bottom: Automatically keeps the latest messages in view ---
    scrollToBottom() {
        if (this.messagesEl) {
            // UI UX: Use requestAnimationFrame for a smooth, flicker-free scroll
            requestAnimationFrame(() => {
                this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
            });
        }
    },

    // --- Is At Bottom: Checks if the user is currently looking at the end of the chat ---
    isAtBottom() {
        if (!this.messagesEl) return true;
        // Logic: Return true if the user is within 80px of the bottom
        return (this.messagesEl.scrollHeight - this.messagesEl.scrollTop - this.messagesEl.clientHeight) < 80;
    },

    // --- Get Date Label: Converts a timestamp into a human-friendly string ---
    getDateLabel(date) {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        // UI UX: Use "Today" and "Yesterday" for better readability
        if (date.toDateString() === today.toDateString()) return 'Today';
        if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
        // Otherwise, show the full date
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    // --- Get Avatar Color: Generates a consistent, unique color for any name ---
    getAvatarColor(name) {
        // UI Design: A premium palette of curated colors
        const colors = [
            '#5C6B4F', '#C0392B', '#2C82C9', '#D4790E', '#27AE60',
            '#8E44AD', '#16A085', '#D35400', '#2C3E50', '#E74C3C',
        ];
        // Logic: Hash the name string to pick a color index
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        return colors[Math.abs(hash) % colors.length];
    },

    // --- Escape HTML: Security measure to prevent XSS (hacker scripts) ---
    escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text)); // Logic: Safely treat text as literal data, not HTML
        return div.innerHTML;
    },
};

// Boot
window.ChatApp = ChatApp;
document.addEventListener('DOMContentLoaded', () => ChatApp.init());
