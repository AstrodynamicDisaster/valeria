// ValerIA Web App - Client-side JavaScript

const API_BASE = '/api';
let sessionId = localStorage.getItem('valeria_session_id') || null;
let isProcessing = false;

// DOM elements
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const clearBtn = document.getElementById('clearBtn');
const statusBar = document.getElementById('statusBar');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadHistory();

    // Configure marked.js for syntax highlighting
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });
});

function setupEventListeners() {
    // Send message
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });

    // File upload
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Clear conversation
    clearBtn.addEventListener('click', clearConversation);

    // Markdown toolbar
    document.querySelectorAll('.md-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            insertMarkdown(btn.dataset.md);
        });
    });

    // Keyboard shortcuts for markdown
    messageInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'b') {
                e.preventDefault();
                insertMarkdown('**');
            } else if (e.key === 'i') {
                e.preventDefault();
                insertMarkdown('*');
            }
        }
    });
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Add user message to chat
    addMessage('user', message);

    // Show loading
    const loadingId = addLoadingMessage();
    setProcessing(true);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        // Update session ID
        if (data.session_id) {
            sessionId = data.session_id;
            localStorage.setItem('valeria_session_id', sessionId);
        }

        // Remove loading and add response
        removeMessage(loadingId);
        addMessage('assistant', data.response);

    } catch (error) {
        removeMessage(loadingId);
        addErrorMessage(`Error: ${error.message}`);
    } finally {
        setProcessing(false);
    }
}

async function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    fileName.textContent = file.name;

    // Create session if needed
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('valeria_session_id', sessionId);
    }

    // Upload file
    setProcessing(true);
    updateStatus(`Uploading ${file.name}...`);

    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }

        // Add upload confirmation
        addMessage('user', `📎 Uploaded: ${file.name}`);
        addMessage('assistant', data.message);

        // Auto-process the file
        messageInput.value = `Process the file I just uploaded: ${data.file_path}`;
        await sendMessage();

    } catch (error) {
        addErrorMessage(`Upload error: ${error.message}`);
    } finally {
        setProcessing(false);
        updateStatus('Ready');
        fileInput.value = '';
        fileName.textContent = '';
    }
}

async function loadHistory() {
    if (!sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/history?session_id=${sessionId}`);
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            // Clear welcome message
            chatContainer.innerHTML = '';

            // Add messages from history
            data.history.forEach(msg => {
                if (msg.role === 'user' || msg.role === 'assistant') {
                    addMessage(msg.role, msg.content, false);
                }
            });
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

async function clearConversation() {
    if (!confirm('Clear conversation history?')) return;

    try {
        if (sessionId) {
            await fetch(`${API_BASE}/clear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: sessionId })
            });
        }

        // Clear local state
        sessionId = null;
        localStorage.removeItem('valeria_session_id');

        // Reset UI
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to ValerIA! 👋</h2>
                <p>I can help you with:</p>
                <ul>
                    <li>📄 Import employee data from vida laboral CSV</li>
                    <li>📋 Process payroll documents (nominas) from PDF files</li>
                    <li>🏢 Manage companies, employees, and payroll records</li>
                    <li>📊 Generate reports and detect missing payslips</li>
                </ul>
                <p class="tip">💡 Try: "Show me all companies" or upload a file to get started!</p>
            </div>
        `;

        updateStatus('Ready');
    } catch (error) {
        console.error('Failed to clear conversation:', error);
    }
}

function addMessage(role, content, scroll = true) {
    // Remove welcome message if present
    const welcomeMsg = chatContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const icon = role === 'user'
        ? '👤'
        : '<img src="valeria.png" alt="ValerIA" class="logo-message">';

    messageDiv.innerHTML = `
        <div class="message-icon">${icon}</div>
        <div class="message-content">${formatMessage(content)}</div>
    `;

    chatContainer.appendChild(messageDiv);

    if (scroll) {
        scrollToBottom();
    }

    return messageDiv;
}

function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant loading';
    messageDiv.id = 'loading-' + Date.now();

    messageDiv.innerHTML = `
        <div class="message-icon"><img src="valeria.png" alt="ValerIA" class="logo-message"></div>
        <div class="message-content">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;

    chatContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv.id;
}

function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

function addErrorMessage(content) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = content;

    chatContainer.appendChild(errorDiv);
    scrollToBottom();

    // Auto-remove after 5 seconds
    setTimeout(() => errorDiv.remove(), 5000);
}

function formatMessage(content) {
    // Use marked.js for full markdown rendering
    return marked.parse(content);
}

function insertMarkdown(syntax) {
    const start = messageInput.selectionStart;
    const end = messageInput.selectionEnd;
    const text = messageInput.value;
    const selectedText = text.substring(start, end);

    let insertion;
    let cursorOffset;

    if (syntax === '```') {
        // Code block - multi-line
        insertion = selectedText
            ? `\`\`\`\n${selectedText}\n\`\`\``
            : '\`\`\`\n\n\`\`\`';
        cursorOffset = selectedText ? insertion.length : 4;
    } else if (syntax === '- ') {
        // List item
        insertion = selectedText ? `- ${selectedText}` : '- ';
        cursorOffset = insertion.length;
    } else if (syntax === '[]()') {
        // Link
        insertion = selectedText ? `[${selectedText}]()` : '[]()'
        cursorOffset = selectedText ? insertion.length - 1 : 1;
    } else {
        // Wrapping syntax (bold, italic, code)
        insertion = selectedText
            ? `${syntax}${selectedText}${syntax}`
            : `${syntax}${syntax}`;
        cursorOffset = selectedText ? insertion.length : syntax.length;
    }

    // Insert the markdown
    messageInput.value = text.substring(0, start) + insertion + text.substring(end);

    // Set cursor position
    const newCursorPos = start + cursorOffset;
    messageInput.setSelectionRange(newCursorPos, newCursorPos);
    messageInput.focus();

    // Trigger auto-resize
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setProcessing(processing) {
    isProcessing = processing;
    sendBtn.disabled = processing;
    uploadBtn.disabled = processing;
    messageInput.disabled = processing;

    if (processing) {
        updateStatus('Processing...');
    } else {
        updateStatus('Ready');
    }
}

function updateStatus(message) {
    statusBar.textContent = message;
}

function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Handle visibility change to reload history
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && sessionId) {
        loadHistory();
    }
});
