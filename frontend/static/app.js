// ==========================================================================
// FIREBASE AUTH CONFIGURATION & INITIALIZATION
// ==========================================================================

// Default config. Swap these values with your actual Firebase project settings!
const firebaseConfig = {
    apiKey: "AIzaSyDummyKey-ForTestingOnly",
    authDomain: "intellisupport-swarm.firebaseapp.com",
    projectId: "intellisupport-swarm",
    storageBucket: "intellisupport-swarm.appspot.com",
    messagingSenderId: "1234567890",
    appId: "1:1234567890:web:123456abc"
};

// Check if using placeholder key to enable Mock Simulator
const isDemoMode = firebaseConfig.apiKey.includes("DummyKey");

// Initialize Firebase App
let auth;
try {
    firebase.initializeApp(firebaseConfig);
    auth = firebase.auth();
} catch (e) {
    console.error("Firebase Auth failed to initialize. Falling back to Demo Simulator.", e);
}

// Global Auth State
let currentUser = null;
let confirmationResult = null; // For phone OTP verification

// ==========================================================================
// AUTH STATE MANAGEMENT (Google & Phone Sign-in)
// ==========================================================================

// Global hook to toggle tabs on Login screen
window.switchLoginTab = function(type) {
    const tabGoogle = document.getElementById("tab-google");
    const tabPhone = document.getElementById("tab-phone");
    const panelGoogle = document.getElementById("panel-google");
    const panelPhone = document.getElementById("panel-phone");
    const errBox = document.getElementById("auth-error");
    
    // Reset errors
    errBox.style.display = "none";
    
    if (type === "google") {
        tabGoogle.classList.add("active");
        tabPhone.classList.remove("active");
        panelGoogle.classList.add("active");
        panelPhone.classList.remove("active");
    } else {
        tabPhone.classList.add("active");
        tabGoogle.classList.remove("active");
        panelPhone.classList.add("active");
        panelGoogle.classList.remove("active");
        
        // Initialize ReCAPTCHA if needed
        initRecaptcha();
    }
};

// Initialize Recaptcha for Phone verification
let recaptchaVerifier = null;
function initRecaptcha() {
    if (recaptchaVerifier || isDemoMode) return;
    try {
        recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container', {
            'size': 'normal',
            'callback': (response) => {
                // reCAPTCHA solved
            }
        });
        recaptchaVerifier.render();
    } catch (e) {
        console.error("Recaptcha initialization failed", e);
        showAuthError("Recaptcha verification loading failed.");
    }
}

// Show validation errors on login card
function showAuthError(message) {
    const errBox = document.getElementById("auth-error");
    errBox.textContent = message;
    errBox.style.display = "block";
}

// Handle login state changes
function handleAuthStateChange(user) {
    const loginOverlay = document.getElementById("login-overlay");
    const profileCard = document.getElementById("user-profile-card");
    const userNameEl = document.getElementById("user-display-name");
    const userIdentifierEl = document.getElementById("user-identifier");
    const userAvatarEl = document.getElementById("user-avatar");
    
    if (user) {
        currentUser = user;
        loginOverlay.style.display = "none";
        profileCard.style.display = "flex";
        
        // Populate profile card
        const displayName = user.displayName || user.phoneNumber || "AI Support User";
        const identifier = user.email || user.phoneNumber || "Authenticated User";
        userNameEl.textContent = displayName;
        userIdentifierEl.textContent = identifier;
        
        // Set avatar (default or Google photo)
        if (user.photoURL) {
            userAvatarEl.src = user.photoURL;
        } else {
            // Generate letter-avatar using initials
            const initial = displayName.charAt(0).toUpperCase();
            userAvatarEl.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=4F46E5&color=fff&size=64`;
        }
        
        // Initialize sessions scoped to this user
        initSessions();
    } else {
        currentUser = null;
        loginOverlay.style.display = "flex";
        profileCard.style.display = "none";
        
        // Reset state
        sessions = {};
        currentSessionId = "";
        
        // Switch back to google tab
        switchLoginTab("google");
    }
}

// ==========================================================================
// SESSION STATE AND PERSISTENCE (Scoped to currentUser.uid)
// ==========================================================================
let sessions = {};
let currentSessionId = "";

// Initialize sessions from LocalStorage scoped to User ID
function initSessions() {
    if (!currentUser) return;
    
    const storageKey = `intellisupport_sessions_${currentUser.uid}`;
    const stored = localStorage.getItem(storageKey);
    
    if (stored) {
        try {
            sessions = JSON.parse(stored);
        } catch (e) {
            console.error("Failed to parse stored sessions, clearing", e);
            sessions = {};
        }
    } else {
        sessions = {};
    }
    
    const sessionKeys = Object.keys(sessions);
    if (sessionKeys.length === 0) {
        createNewSession();
    } else {
        // Load the most recently active session for this user
        const storedActiveId = localStorage.getItem(`intellisupport_active_session_${currentUser.uid}`);
        if (storedActiveId && sessions[storedActiveId]) {
            currentSessionId = storedActiveId;
        } else {
            currentSessionId = sessionKeys[0];
        }
        renderSidebar();
        loadActiveChat();
    }
}

// Save sessions state to LocalStorage scoped to User ID
function saveSessions() {
    if (!currentUser) return;
    
    const storageKey = `intellisupport_sessions_${currentUser.uid}`;
    localStorage.setItem(storageKey, JSON.stringify(sessions));
    localStorage.setItem(`intellisupport_active_session_${currentUser.uid}`, currentSessionId);
}

// Create new chat session
function createNewSession() {
    const sid = "session_" + Date.now() + "_" + Math.floor(Math.random() * 1000);
    sessions[sid] = {
        id: sid,
        title: "New Conversation",
        messages: [],
        timestamp: Date.now()
    };
    currentSessionId = sid;
    saveSessions();
    renderSidebar();
    loadActiveChat();
    
    // Focus the chat input on new chat creation
    const chatInput = document.getElementById("chat-input");
    if (chatInput) chatInput.focus();
}

// Rename session
function renameSession(sid) {
    if (!sessions[sid]) return;
    const oldTitle = sessions[sid].title;
    const newTitle = prompt("Rename conversation:", oldTitle);
    if (newTitle !== null && newTitle.trim() !== "") {
        sessions[sid].title = newTitle.trim();
        saveSessions();
        renderSidebar();
        if (sid === currentSessionId) {
            document.getElementById("active-chat-title").textContent = newTitle.trim();
        }
    }
}

// Delete session
function deleteSession(sid) {
    if (!sessions[sid]) return;
    if (confirm(`Are you sure you want to delete the conversation "${sessions[sid].title}"?`)) {
        delete sessions[sid];
        const keys = Object.keys(sessions);
        if (keys.length === 0) {
            createNewSession();
        } else {
            if (currentSessionId === sid) {
                currentSessionId = keys[0];
            }
            saveSessions();
            renderSidebar();
            loadActiveChat();
        }
    }
}

// Select session
function selectSession(sid) {
    if (sid === currentSessionId) return;
    currentSessionId = sid;
    saveSessions();
    renderSidebar();
    loadActiveChat();
}

// Predict agent based on routing keywords (matching backend agents/router.py)
function predictAgent(query) {
    const q = query.toLowerCase();
    if (["bill", "billing", "payment", "refund", "invoice"].some(w => q.includes(w))) {
        return "billing";
    } else if (["error", "bug", "login", "issue", "technical"].some(w => q.includes(w))) {
        return "technical";
    } else if (["order", "delivery", "shipping", "track"].some(w => q.includes(w))) {
        return "order";
    }
    return "faq";
}

// Get Agent Config details (Label & Icon)
const AGENT_CONFIGS = {
    router: { label: "Router", icon: "insights" },
    billing: { label: "Billing Specialist", icon: "account_balance_wallet" },
    technical: { label: "Technical Support", icon: "build" },
    order: { label: "Orders Specialist", icon: "local_shipping" },
    faq: { label: "FAQ Assistant", icon: "help_center" }
};

// ==========================================================================
// RENDERING FUNCTIONS
// ==========================================================================

// Render chat list in Sidebar
function renderSidebar() {
    const listContainer = document.getElementById("chat-history-list");
    listContainer.innerHTML = "";
    
    // Sort sessions by timestamp descending (newest first)
    const sortedSessions = Object.values(sessions).sort((a, b) => b.timestamp - a.timestamp);
    
    sortedSessions.forEach(session => {
        const item = document.createElement("div");
        item.className = `history-item ${session.id === currentSessionId ? "active" : ""}`;
        item.setAttribute("onclick", `selectSession('${session.id}')`);
        
        const iconName = "chat_bubble";
        
        item.innerHTML = `
            <div class="history-item-content">
                <span class="material-symbols-rounded icon">${iconName}</span>
                <span class="history-item-title">${escapeHTML(session.title)}</span>
            </div>
            <div class="history-actions-hidden">
                <button class="hist-action-btn" onclick="event.stopPropagation(); renameSession('${session.id}')" title="Rename">
                    <span class="material-symbols-rounded">edit</span>
                </button>
                <button class="hist-action-btn btn-delete" onclick="event.stopPropagation(); deleteSession('${session.id}')" title="Delete">
                    <span class="material-symbols-rounded">delete</span>
                </button>
            </div>
        `;
        listContainer.appendChild(item);
    });
}

// Load active conversation messages
function loadActiveChat() {
    const activeChat = sessions[currentSessionId];
    if (!activeChat) return;
    
    const threadContainer = document.getElementById("chat-thread");
    const welcomeContainer = document.getElementById("welcome-container");
    
    // Update Header metadata
    document.getElementById("active-chat-title").textContent = activeChat.title;
    document.getElementById("message-count").textContent = `${activeChat.messages.length} messages`;
    
    // Clear all HUD active animations
    resetHUDNodes();
    
    // Toggle Welcome empty state card
    if (activeChat.messages.length === 0) {
        welcomeContainer.style.display = "flex";
        
        // Remove old bubbles
        const bubbles = threadContainer.querySelectorAll(".message-bubble");
        bubbles.forEach(b => b.remove());
    } else {
        welcomeContainer.style.display = "none";
        
        // Remove old bubbles
        const bubbles = threadContainer.querySelectorAll(".message-bubble");
        bubbles.forEach(b => b.remove());
        
        activeChat.messages.forEach(msg => {
            appendMessageBubble(msg.role, msg.content, msg.agent);
        });
        
        scrollToBottom();
    }
}

// Escape HTML utility to prevent XSS
function escapeHTML(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
}

// Append message bubble to chat thread view
function appendMessageBubble(role, content, agentKey) {
    const threadContainer = document.getElementById("chat-thread");
    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role}`;
    
    const avatarIcon = role === "user" ? "person" : "smart_toy";
    
    let badgeHtml = "";
    if (role === "assistant" && agentKey && AGENT_CONFIGS[agentKey]) {
        const conf = AGENT_CONFIGS[agentKey];
        badgeHtml = `
            <div class="agent-badge-pill ${agentKey}">
                <span class="material-symbols-rounded">${conf.icon}</span>
                <span>${conf.label}</span>
            </div>
        `;
    }
    
    let formattedContent = escapeHTML(content).replace(/\n/g, "<br>");
    formattedContent = formattedContent.replace(/\*\*(.*?)\*\"/g, "<strong>$1</strong>");
    
    bubble.innerHTML = `
        <div class="message-avatar">
            <span class="material-symbols-rounded">${avatarIcon}</span>
        </div>
        <div class="message-content-wrapper">
            ${badgeHtml}
            <div class="message-bubble-body">
                ${formattedContent}
            </div>
        </div>
    `;
    
    threadContainer.appendChild(bubble);
}

// Auto-scroll chat thread to bottom
function scrollToBottom() {
    const threadContainer = document.getElementById("chat-thread");
    threadContainer.scrollTop = threadContainer.scrollHeight;
}

// ==========================================================================
// MULTI-AGENT SWARM HUD ANIMATIONS
// ==========================================================================

// Set specific agent node as active
function activateHUDNode(agentKey, isPulse = false) {
    resetHUDNodes();
    const node = document.getElementById(`agent-${agentKey}`);
    if (node) {
        node.classList.add("active");
        if (isPulse) {
            node.classList.add("routing-pulse");
        }
    }
}

// Reset all HUD agent nodes to default state
function resetHUDNodes() {
    const nodes = document.querySelectorAll(".agent-node");
    nodes.forEach(node => {
        node.className = "agent-node";
    });
}

// Show Typing Indicator
function showTypingIndicator(stage, agentKey) {
    const indicator = document.getElementById("typing-indicator");
    const badge = document.getElementById("typing-agent-badge");
    
    if (stage === "routing") {
        badge.innerHTML = `
            <span class="material-symbols-rounded">insights</span>
            <span>Router selecting agent...</span>
        `;
        activateHUDNode("router", true);
    } else if (stage === "thinking" && agentKey && AGENT_CONFIGS[agentKey]) {
        const conf = AGENT_CONFIGS[agentKey];
        badge.innerHTML = `
            <span class="material-symbols-rounded">${conf.icon}</span>
            <span>${conf.label} thinking...</span>
        `;
        activateHUDNode(agentKey, true);
    }
    
    indicator.style.display = "flex";
    scrollToBottom();
}

// Hide Typing Indicator
function hideTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    indicator.style.display = "none";
    resetHUDNodes();
}

// ==========================================================================
// BACKEND API AND CONNECTION STATUS
// ==========================================================================

// Check backend status
async function checkBackendStatus() {
    const pingGlow = document.getElementById("api-ping-glow");
    const statusText = document.getElementById("api-status-text");
    
    try {
        const resp = await fetch("/health", { method: "GET" });
        if (resp.ok) {
            pingGlow.className = "status-ping online";
            statusText.textContent = "Backend online";
        } else {
            throw new Error();
        }
    } catch (e) {
        pingGlow.className = "status-ping offline";
        statusText.textContent = "Backend offline";
    }
}

// Send Message Flow
async function sendMessage(text) {
    if (!text || text.trim() === "") return;
    if (!currentUser) return;
    
    const activeChat = sessions[currentSessionId];
    const userPrompt = text.trim();
    
    // 1. If first message, rename conversation title based on prompt
    const isFirstMessage = activeChat.messages.length === 0;
    if (isFirstMessage) {
        activeChat.title = userPrompt.length > 25 ? userPrompt.substring(0, 24) + "..." : userPrompt;
        document.getElementById("active-chat-title").textContent = activeChat.title;
        document.getElementById("welcome-container").style.display = "none";
    }
    
    // 2. Add User message to local storage & Render bubble
    const userMsg = { role: "user", content: userPrompt };
    activeChat.messages.push(userMsg);
    activeChat.timestamp = Date.now();
    saveSessions();
    renderSidebar();
    
    appendMessageBubble("user", userPrompt);
    document.getElementById("message-count").textContent = `${activeChat.messages.length} messages`;
    scrollToBottom();
    
    // Disable inputs
    setInputDisabledState(true);
    
    // 3. MULTI-AGENT ANIMATION PIPELINE
    
    // A. Start with Router
    showTypingIndicator("routing");
    
    // Predict which agent it will land on based on user prompt keywords
    const predictedAgent = predictAgent(userPrompt);
    
    // Wait 1.2s to simulate router checking policy database & directing traffic
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    // B. Switch to target agent thinking state
    showTypingIndicator("thinking", predictedAgent);
    
    // C. Make backend API request
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: userPrompt })
        });
        
        // Wait at least another 500ms to avoid flashing if backend responds too fast
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (response.ok) {
            const data = await response.json();
            const botAnswer = data.response || "No response generated.";
            
            // Add bot message
            const botMsg = { role: "assistant", content: botAnswer, agent: predictedAgent };
            activeChat.messages.push(botMsg);
            saveSessions();
            
            appendMessageBubble("assistant", botAnswer, predictedAgent);
        } else {
            throw new Error(`Server Error (${response.status})`);
        }
    } catch (err) {
        console.error("API Call Failed", err);
        const errorAnswer = `An error occurred: ${err.message || err}. Please ensure your backend server is running correctly.`;
        appendMessageBubble("assistant", errorAnswer, "router");
    } finally {
        hideTypingIndicator();
        setInputDisabledState(false);
        document.getElementById("message-count").textContent = `${activeChat.messages.length} messages`;
        scrollToBottom();
    }
}

// ==========================================================================
// USER INTERFACES & INPUT HANDLERS
// ==========================================================================

function setInputDisabledState(disabled) {
    const input = document.getElementById("chat-input");
    const btn = document.getElementById("btn-send");
    
    input.disabled = disabled;
    btn.disabled = disabled || input.value.trim() === "";
}

window.fillPrompt = function(promptText) {
    const input = document.getElementById("chat-input");
    input.value = promptText;
    adjustTextareaHeight(input);
    
    const btn = document.getElementById("btn-send");
    btn.disabled = false;
    
    input.focus();
};

function adjustTextareaHeight(el) {
    el.style.height = "auto";
    const newHeight = Math.min(el.scrollHeight, 180);
    el.style.height = newHeight + "px";
}

// ==========================================================================
// DOM CONTENT LOADED - ENTRY POINT
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. FIREBASE AUTHENTICATION EVENT HANDLERS ---
    
    const btnGoogle = document.getElementById("btn-google-signin");
    const phoneForm = document.getElementById("phone-login-form");
    const otpForm = document.getElementById("otp-verify-form");
    const btnChangePhone = document.getElementById("btn-change-phone");
    const btnLogout = document.getElementById("btn-logout");
    const errBox = document.getElementById("auth-error");
    
    // Google Login Trigger
    btnGoogle.addEventListener("click", () => {
        errBox.style.display = "none";
        
        if (isDemoMode) {
            // Simulated login flow for instant demo testing
            console.log("Running in Google Demo Mode...");
            showAuthError("Demo Mode: Simulating Google authentication...");
            
            setTimeout(() => {
                const demoUser = {
                    uid: "demo_google_user_123",
                    displayName: "Mehak Sharma",
                    email: "mehak.sharma@gmail.com",
                    photoURL: ""
                };
                handleAuthStateChange(demoUser);
            }, 1000);
            return;
        }
        
        const provider = new firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(provider)
            .then(result => {
                handleAuthStateChange(result.user);
            })
            .catch(error => {
                console.error("Google Sign-In Error", error);
                showAuthError(`Google Sign-In Failed: ${error.message}`);
            });
    });
    
    // Phone OTP request
    phoneForm.addEventListener("submit", (e) => {
        e.preventDefault();
        errBox.style.display = "none";
        
        let phoneNumber = document.getElementById("phone-number").value.trim();
        // Simple sanitization: prepend +1 if no plus symbol exists
        if (!phoneNumber.startsWith("+")) {
            phoneNumber = "+1" + phoneNumber.replace(/[-\s()]/g, "");
        }
        
        if (isDemoMode) {
            console.log("Running in Phone Demo Mode for:", phoneNumber);
            showAuthError("Demo Mode: SMS simulated. Enter code '123456' to log in.");
            
            setTimeout(() => {
                phoneForm.style.display = "none";
                otpForm.style.display = "flex";
                document.getElementById("otp-code").focus();
            }, 800);
            return;
        }
        
        const appVerifier = recaptchaVerifier;
        auth.signInWithPhoneNumber(phoneNumber, appVerifier)
            .then(result => {
                confirmationResult = result;
                phoneForm.style.display = "none";
                otpForm.style.display = "flex";
                document.getElementById("otp-code").focus();
            })
            .catch(error => {
                console.error("Phone Auth Error", error);
                showAuthError(`SMS request failed: ${error.message}`);
                // Reset recaptcha
                if (window.grecaptcha) {
                    grecaptcha.reset();
                }
            });
    });
    
    // OTP verification
    otpForm.addEventListener("submit", (e) => {
        e.preventDefault();
        errBox.style.display = "none";
        
        const code = document.getElementById("otp-code").value.trim();
        
        if (isDemoMode) {
            if (code === "123456") {
                const demoUser = {
                    uid: "demo_phone_user_456",
                    displayName: "Customer Support User",
                    email: "",
                    phoneNumber: "+1 555-0199",
                    photoURL: ""
                };
                handleAuthStateChange(demoUser);
            } else {
                showAuthError("Demo Error: Invalid code. Please enter '123456'.");
            }
            return;
        }
        
        if (!confirmationResult) {
            showAuthError("Session expired. Please try sending SMS again.");
            return;
        }
        
        confirmationResult.confirm(code)
            .then(result => {
                handleAuthStateChange(result.user);
            })
            .catch(error => {
                console.error("OTP Verification Error", error);
                showAuthError(`Invalid verification code: ${error.message}`);
            });
    });
    
    // Return back to Phone entry
    btnChangePhone.addEventListener("click", () => {
        otpForm.style.display = "none";
        phoneForm.style.display = "flex";
        errBox.style.display = "none";
        document.getElementById("otp-code").value = "";
    });
    
    // Logout Handler
    btnLogout.addEventListener("click", () => {
        if (isDemoMode) {
            handleAuthStateChange(null);
            return;
        }
        
        auth.signOut()
            .then(() => {
                handleAuthStateChange(null);
            })
            .catch(error => {
                console.error("Logout error", error);
                alert("Sign Out failed: " + error.message);
            });
    });
    
    // Firebase auth status subscription
    if (!isDemoMode && auth) {
        auth.onAuthStateChanged(user => {
            handleAuthStateChange(user);
        });
    } else {
        // Initially logged out in Demo Mode
        handleAuthStateChange(null);
    }
    
    // --- 2. REGULAR CHAT FUNCTIONAL INTERACTION LISTENERS ---
    
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("btn-send");
    const chatForm = document.getElementById("chat-form");
    const newChatBtn = document.getElementById("btn-new-chat");
    const deleteChatBtn = document.getElementById("btn-delete-chat");
    const renameChatBtn = document.getElementById("btn-rename-chat");
    
    // Auto grow textarea as user types
    chatInput.addEventListener("input", function() {
        adjustTextareaHeight(this);
        sendBtn.disabled = this.value.trim() === "" || !currentUser;
    });
    
    // Send message on Enter key press (without shift key)
    chatInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() !== "" && !this.disabled && currentUser) {
                chatForm.requestSubmit();
            }
        }
    });
    
    // Form submission
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = chatInput.value;
        chatInput.value = "";
        adjustTextareaHeight(chatInput);
        sendBtn.disabled = true;
        
        sendMessage(text);
    });
    
    // Action buttons
    newChatBtn.addEventListener("click", () => {
        if (currentUser) createNewSession();
    });
    deleteChatBtn.addEventListener("click", () => {
        if (currentUser) deleteSession(currentSessionId);
    });
    renameChatBtn.addEventListener("click", () => {
        if (currentUser) renameSession(currentSessionId);
    });
    
    // Initial backend status check and start interval (every 8 seconds)
    checkBackendStatus();
    setInterval(checkBackendStatus, 8000);
});
