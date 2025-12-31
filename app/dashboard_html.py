"""HTML Dashboard served directly from FastAPI."""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Warden</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --bg-hover: #22222f;
            --border: #2a2a3a;
            --text-primary: #f0f0f5;
            --text-secondary: #9090a0;
            --text-muted: #606070;
            --accent: #ff3b3b;
            --accent-dim: #cc2f2f;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
        }

        .app-container { display: flex; min-height: 100vh; }

        .sidebar {
            width: 260px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 24px 16px;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
        }

        .main-content {
            flex: 1;
            margin-left: 260px;
            padding: 32px 40px;
            max-width: 1200px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0 12px 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent), #ff6b6b);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .logo-text { font-weight: 700; font-size: 18px; }
        .logo-text span { color: var(--accent); }

        .nav-section { margin-bottom: 32px; }

        .nav-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            padding: 0 12px;
            margin-bottom: 8px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
        }

        .nav-item:hover { background: var(--bg-hover); color: var(--text-primary); }
        .nav-item.active { background: var(--bg-tertiary); color: var(--text-primary); }
        .nav-item .icon { font-size: 18px; width: 24px; text-align: center; }

        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title { font-size: 16px; font-weight: 600; }

        .page-header { margin-bottom: 32px; }
        .page-title { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
        .page-subtitle { color: var(--text-secondary); font-size: 15px; }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }

        @media (max-width: 1100px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }

        .metric-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: var(--accent);
        }

        .metric-card.success::before { background: var(--success); }
        .metric-card.warning::before { background: var(--warning); }
        .metric-card.info::before { background: var(--info); }

        .metric-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
        .metric-value { font-size: 32px; font-weight: 700; }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: all 0.15s;
            font-family: inherit;
        }

        .btn-primary { background: var(--accent); color: white; }
        .btn-primary:hover { background: var(--accent-dim); }
        .btn-secondary { background: var(--bg-tertiary); color: var(--text-primary); border: 1px solid var(--border); }
        .btn-secondary:hover { background: var(--bg-hover); }
        .btn-success { background: var(--success); color: white; }
        .btn-warning { background: var(--warning); color: black; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-sm { padding: 6px 12px; font-size: 13px; }

        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 13px; font-weight: 500; color: var(--text-secondary); margin-bottom: 8px; }

        .form-input, .form-textarea {
            width: 100%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
        }

        .form-input:focus, .form-textarea:focus { outline: none; border-color: var(--accent); }

        .form-textarea {
            min-height: 120px;
            resize: vertical;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }

        .chat-container {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            height: 500px;
            display: flex;
            flex-direction: column;
        }

        .chat-messages { flex: 1; overflow-y: auto; padding: 20px; }

        .chat-message {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            max-width: 85%;
        }

        .chat-message.warden { margin-right: auto; }
        .chat-message.user { margin-left: auto; flex-direction: row-reverse; }

        .chat-avatar {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }

        .chat-message.warden .chat-avatar { background: linear-gradient(135deg, var(--accent), #ff6b6b); }
        .chat-message.user .chat-avatar { background: var(--bg-tertiary); border: 1px solid var(--border); }

        .chat-bubble {
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
        }

        .chat-message.warden .chat-bubble { background: var(--bg-secondary); border: 1px solid var(--border); border-bottom-left-radius: 4px; }
        .chat-message.user .chat-bubble { background: var(--bg-tertiary); border-bottom-right-radius: 4px; }
        .chat-time { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
        .chat-type { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--accent); margin-bottom: 4px; }

        .chat-input-container {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            background: var(--bg-secondary);
        }

        .chat-input-container form {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 12px 20px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.15s;
        }

        .chat-input:focus {
            border-color: var(--accent);
        }

        .chat-input::placeholder {
            color: var(--text-muted);
        }

        .chat-send-btn {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--accent);
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s;
            flex-shrink: 0;
        }

        .chat-send-btn:hover {
            background: var(--accent-dim);
            transform: scale(1.05);
        }

        .chat-send-btn:disabled {
            background: var(--bg-tertiary);
            color: var(--text-muted);
            cursor: not-allowed;
            transform: none;
        }

        .chat-send-btn.loading {
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid var(--border);
        }
        .list-item:last-child { border-bottom: none; }
        .list-item-title { font-weight: 500; margin-bottom: 4px; }
        .list-item-meta { font-size: 13px; color: var(--text-secondary); }
        .list-item-actions { display: flex; gap: 8px; }

        .pattern-item {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 3px solid var(--danger);
        }
        .pattern-item.medium { border-left-color: var(--warning); }
        .pattern-item.low { border-left-color: var(--success); }
        .pattern-type { font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 6px; }
        .pattern-desc { font-size: 14px; color: var(--text-secondary); }

        .tabs {
            display: flex;
            gap: 4px;
            background: var(--bg-tertiary);
            padding: 4px;
            border-radius: 10px;
            margin-bottom: 24px;
        }

        .tab {
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            color: var(--text-secondary);
            background: none;
            border: none;
        }
        .tab:hover { color: var(--text-primary); }
        .tab.active { background: var(--bg-secondary); color: var(--text-primary); }

        .badge {
            display: inline-flex;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge-pending { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
        .badge-completed { background: rgba(34, 197, 94, 0.15); color: var(--success); }
        .badge-failed { background: rgba(239, 68, 68, 0.15); color: var(--danger); }

        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
        .grid-3 { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; }
        @media (max-width: 900px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

        .empty-state { text-align: center; padding: 48px 24px; color: var(--text-muted); }
        .empty-state-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }

        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            padding: 16px 20px;
            border-radius: 10px;
            display: none;
            z-index: 1000;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .toast.success { border-left: 3px solid var(--success); }
        .toast.error { border-left: 3px solid var(--danger); }
        .toast.show { display: block; }

        .auth-overlay {
            position: fixed;
            inset: 0;
            background: var(--bg-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }

        .auth-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            text-align: center;
        }

        .auth-logo {
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, var(--accent), #ff6b6b);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin: 0 auto 24px;
        }

        .auth-title { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
        .auth-subtitle { color: var(--text-secondary); margin-bottom: 32px; }

        .section { display: none; }
        .section.active { display: block; }

        /* Mobile hamburger menu */
        .mobile-header {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 0 16px;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
        }

        .hamburger {
            background: none;
            border: none;
            color: var(--text-primary);
            font-size: 24px;
            cursor: pointer;
            padding: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .mobile-logo {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 16px;
        }

        .mobile-logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--accent), #ff6b6b);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .sidebar-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 199;
        }

        .sidebar-overlay.active { display: block; }

        @media (max-width: 768px) {
            .mobile-header { display: flex; }

            .sidebar {
                position: fixed;
                left: -280px;
                top: 0;
                height: 100vh;
                z-index: 200;
                transition: left 0.3s ease;
                width: 280px;
            }

            .sidebar.open { left: 0; }

            .main-content {
                margin-left: 0;
                padding: 80px 16px 20px;
            }

            .page-title { font-size: 22px; }
            .page-subtitle { font-size: 13px; }
        }

        .model-select {
            width: 100%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%239090a0' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 16px center;
        }
        .model-select:focus { outline: none; border-color: var(--accent); }
        .model-select option { background: var(--bg-secondary); color: var(--text-primary); padding: 8px; }
        .model-select optgroup { background: var(--bg-tertiary); color: var(--text-muted); font-weight: 600; }
        .model-info { margin-top: 12px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px; font-size: 13px; }
        .model-info-label { color: var(--text-muted); margin-bottom: 4px; }
        .model-info-value { color: var(--text-primary); font-family: 'JetBrains Mono', monospace; font-size: 12px; }
        .model-count { font-size: 12px; color: var(--text-secondary); margin-left: 8px; }

        .calendar-event {
            display: flex;
            gap: 16px;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
        }
        .calendar-event:last-child { border-bottom: none; }
        .event-time { width: 70px; font-size: 13px; font-weight: 500; color: var(--accent); }
        .event-title { font-weight: 500; }
        .event-location { font-size: 13px; color: var(--text-muted); }
    </style>
</head>
<body>
    <div id="auth-overlay" class="auth-overlay">
        <div class="auth-card">
            <div class="auth-logo">🔒</div>
            <h1 class="auth-title">The Warden</h1>
            <p class="auth-subtitle">Enter your API key to continue</p>
            <div class="form-group">
                <input type="password" id="apiKeyInput" class="form-input" placeholder="API Key" />
            </div>
            <button class="btn btn-primary" style="width: 100%;" onclick="authenticate()">Connect</button>
        </div>
    </div>

    <!-- Mobile header with hamburger menu -->
    <header class="mobile-header" id="mobile-header" style="display: none;">
        <button class="hamburger" onclick="toggleSidebar()">☰</button>
        <div class="mobile-logo">
            <div class="mobile-logo-icon">🔒</div>
            <span>The Warden</span>
        </div>
        <div style="width: 40px;"></div>
    </header>

    <!-- Overlay for mobile sidebar -->
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="closeSidebar()"></div>

    <div class="app-container" id="app" style="display: none;">
        <aside class="sidebar" id="sidebar">
            <div class="logo">
                <div class="logo-icon">🔒</div>
                <div class="logo-text">The <span>Warden</span></div>
            </div>

            <div class="nav-section">
                <div class="nav-label">Overview</div>
                <div class="nav-item active" onclick="showSection('dashboard')"><span class="icon">📊</span> Dashboard</div>
                <div class="nav-item" onclick="showSection('chat')"><span class="icon">💬</span> Chat History</div>
            </div>

            <div class="nav-section">
                <div class="nav-label">Tracking</div>
                <div class="nav-item" onclick="showSection('commitments')"><span class="icon">✅</span> Commitments</div>
                <div class="nav-item" onclick="showSection('goals')"><span class="icon">🎯</span> Goals</div>
                <div class="nav-item" onclick="showSection('calendar')"><span class="icon">📅</span> Calendar</div>
            </div>

            <div class="nav-section">
                <div class="nav-label">Configuration</div>
                <div class="nav-item" onclick="showSection('settings')"><span class="icon">⚙️</span> Settings</div>
            </div>

            <div class="nav-section">
                <div class="nav-label">System</div>
                <div class="nav-item" onclick="showSection('errors')"><span class="icon">🐛</span> Error Log <span id="error-count-badge" class="badge badge-pending" style="margin-left: auto; display: none;">0</span></div>
            </div>
        </aside>

        <main class="main-content">
            <section id="section-dashboard" class="section active">
                <div class="page-header">
                    <h1 class="page-title">Dashboard</h1>
                    <p class="page-subtitle">Your accountability at a glance</p>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card success"><div class="metric-label">Completion Rate</div><div class="metric-value" id="metric-completion">--%</div></div>
                    <div class="metric-card warning"><div class="metric-label">Pending Tasks</div><div class="metric-value" id="metric-pending">--</div></div>
                    <div class="metric-card info"><div class="metric-label">Response Streak</div><div class="metric-value" id="metric-response-streak">--</div><div class="metric-label" style="margin-top:4px;font-size:11px;" id="streak-response-best"></div></div>
                    <div class="metric-card"><div class="metric-label">Completion Streak</div><div class="metric-value" id="metric-completion-streak">--</div><div class="metric-label" style="margin-top:4px;font-size:11px;" id="streak-completion-best"></div></div>
                </div>

                <div class="grid-3">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Recent Activity</h3>
                            <button class="btn btn-sm btn-secondary" onclick="triggerCheckin()">🔔 Trigger Check-in</button>
                        </div>
                        <div id="recent-activity"><div class="empty-state">Loading...</div></div>
                    </div>
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Active Patterns</h3></div>
                        <div id="patterns-list"><div class="empty-state">Loading...</div></div>
                    </div>
                </div>
            </section>

            <section id="section-chat" class="section">
                <div class="page-header">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h1 class="page-title">Chat History</h1>
                            <p class="page-subtitle">Your conversation with The Warden</p>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <label style="font-size: 12px; color: var(--text-secondary);">LLM Context:</label>
                                <input type="number" id="chat-history-count" class="form-input" style="width: 60px; padding: 4px 8px;" value="15" min="0" max="100" onchange="updateChatHistoryCount(this.value)" />
                                <span style="font-size: 11px; color: var(--text-muted);">messages</span>
                            </div>
                            <button class="btn btn-secondary" onclick="loadChatHistory()">Refresh</button>
                        </div>
                    </div>
                </div>
                <div class="chat-container" style="height: 600px;">
                    <div class="chat-messages" id="chat-messages"><div class="empty-state">Loading...</div></div>
                    <div class="chat-input-container">
                        <form id="chat-form" onsubmit="sendChatMessage(event)">
                            <input type="text" id="chat-input" class="chat-input" placeholder="Message The Warden..." autocomplete="off" />
                            <button type="submit" id="chat-send-btn" class="chat-send-btn" title="Send message">
                                <span id="chat-send-icon">➤</span>
                            </button>
                        </form>
                    </div>
                </div>

                <!-- LLM Memory Section -->
                <div class="card" style="margin-top: 20px;">
                    <div class="card-header" style="cursor: pointer;" onclick="toggleMemoryPanel()">
                        <h3 class="card-title">🧠 Warden's Memory</h3>
                        <span id="memory-toggle-icon" style="font-size: 18px;">▼</span>
                    </div>
                    <div id="memory-panel" style="display: none;">
                        <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 12px;">
                            The Warden's learned observations about you. This updates automatically after conversations.
                        </p>
                        <div class="form-group">
                            <textarea id="llm-memory" class="form-textarea" style="min-height: 200px; font-family: 'JetBrains Mono', monospace; font-size: 12px;"></textarea>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-primary" onclick="saveMemory()">Save Memory</button>
                            <button class="btn btn-secondary" onclick="clearMemory()">Clear All</button>
                        </div>
                    </div>
                </div>

                <!-- Agent Intelligence Section -->
                <div class="card" style="margin-top: 16px;">
                    <div class="card-header" style="cursor: pointer;" onclick="toggleAgentPanel()">
                        <h3 class="card-title">🤖 Agent Intelligence</h3>
                        <span id="agent-toggle-icon" style="font-size: 18px;">▼</span>
                    </div>
                    <div id="agent-panel" style="display: none;">
                        <!-- Accountability Intensity -->
                        <div style="padding: 16px; border-bottom: 1px solid var(--border);">
                            <label class="form-label">Accountability Intensity</label>
                            <div style="display: flex; align-items: center; gap: 16px;">
                                <input type="range" id="intensity-slider" min="1" max="5" value="3"
                                    style="flex: 1;" onchange="updateIntensity(this.value)">
                                <span id="intensity-label" style="min-width: 120px; color: var(--text-secondary);">Balanced (3)</span>
                            </div>
                            <p style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">
                                1 = Gentle & supportive • 3 = Balanced • 5 = Intense & demanding
                            </p>
                        </div>

                        <!-- Thinking Level -->
                        <div style="padding: 16px; border-bottom: 1px solid var(--border);">
                            <label class="form-label">Thinking Level (Reasoning Depth)</label>
                            <div style="display: flex; align-items: center; gap: 12px; margin-top: 8px;">
                                <select id="thinking-level" class="form-input" style="width: auto;" onchange="updateThinkingLevel(this.value)">
                                    <option value="off">Off (Fastest)</option>
                                    <option value="minimal">Minimal</option>
                                    <option value="low">Low</option>
                                    <option value="medium" selected>Medium (Recommended)</option>
                                    <option value="high">High (Deepest)</option>
                                </select>
                                <span id="thinking-cost" style="font-size: 12px; color: var(--text-muted);">💰 Moderate cost</span>
                            </div>
                            <p style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">
                                Higher = better judgment but slower & more expensive. For Gemini 3 Flash and other thinking models.
                            </p>
                        </div>

                        <!-- Mood Trend -->
                        <div style="padding: 16px; border-bottom: 1px solid var(--border);">
                            <label class="form-label">Mood Trend (Last 7 Days)</label>
                            <div id="mood-trend" style="display: flex; gap: 16px; margin-top: 8px;">
                                <div style="text-align: center;">
                                    <div style="font-size: 24px;" id="avg-mood-icon">😐</div>
                                    <div style="font-size: 12px; color: var(--text-muted);">Avg Mood</div>
                                    <div id="avg-mood-value" style="font-weight: 600;">--</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-size: 24px;">⚡</div>
                                    <div style="font-size: 12px; color: var(--text-muted);">Avg Energy</div>
                                    <div id="avg-energy-value" style="font-weight: 600;">--</div>
                                </div>
                            </div>
                        </div>

                        <!-- Scheduled Follow-ups -->
                        <div style="padding: 16px;">
                            <label class="form-label">Scheduled Follow-ups</label>
                            <div id="followups-list" style="margin-top: 8px;">
                                <div class="empty-state" style="padding: 16px; font-size: 13px;">No scheduled follow-ups</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section id="section-commitments" class="section">
                <div class="page-header">
                    <h1 class="page-title">Commitments</h1>
                    <p class="page-subtitle">Track what you've promised to deliver</p>
                </div>
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Add Commitment</h3></div>
                    <form onsubmit="createCommitment(event)">
                        <div class="grid-2">
                            <div class="form-group"><label class="form-label">What are you committing to?</label><input type="text" id="commit-title" class="form-input" required /></div>
                            <div class="form-group">
                                <label class="form-label">Due Date & Time</label>
                                <div style="display: flex; gap: 8px;">
                                    <input type="date" id="commit-due" class="form-input" style="flex: 1;" />
                                    <input type="time" id="commit-time" class="form-input" style="width: 120px;" value="12:00" />
                                </div>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Commitment</button>
                    </form>
                </div>
                <div class="tabs">
                    <button class="tab active" onclick="filterCommitments('pending')">Pending</button>
                    <button class="tab" onclick="filterCommitments('completed')">Completed</button>
                    <button class="tab" onclick="filterCommitments('failed')">Failed</button>
                </div>
                <div class="card"><div id="commitments-list"><div class="empty-state">Loading...</div></div></div>
            </section>

            <section id="section-goals" class="section">
                <div class="page-header">
                    <h1 class="page-title">Goals</h1>
                    <p class="page-subtitle">What are you working toward?</p>
                </div>
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Add Goal</h3></div>
                    <form onsubmit="createGoal(event)">
                        <div class="form-group"><label class="form-label">Goal Title</label><input type="text" id="goal-title" class="form-input" required /></div>
                        <div class="grid-2">
                            <div class="form-group"><label class="form-label">Description</label><input type="text" id="goal-desc" class="form-input" /></div>
                            <div class="form-group"><label class="form-label">Target Date</label><input type="date" id="goal-date" class="form-input" /></div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Goal</button>
                    </form>
                </div>
                <div class="card">
                    <div class="card-header"><h3 class="card-title">Active Goals</h3></div>
                    <div id="goals-list"><div class="empty-state">Loading...</div></div>
                </div>
            </section>

            <section id="section-calendar" class="section">
                <div class="page-header">
                    <h1 class="page-title">Calendar</h1>
                    <p class="page-subtitle">Upcoming events, commitments, and deadlines</p>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header">
                        <h3 class="card-title">Google Calendar Status</h3>
                        <span id="calendar-sync-status" class="badge badge-pending">Not synced</span>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                        <button class="btn btn-primary" onclick="syncCalendar()">Sync Google Calendar</button>
                        <button class="btn btn-secondary" onclick="addManualEvent()">+ Manual Event</button>
                        <span id="last-sync-info" style="color: var(--text-muted); font-size: 13px;"></span>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header">
                        <h3 class="card-title">📋 Upcoming Commitments</h3>
                        <span id="commitment-count" class="badge badge-pending">0</span>
                    </div>
                    <div id="calendar-commitments"><div class="empty-state">No pending commitments with deadlines</div></div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">📅 Calendar Events (14 days)</h3>
                        <span id="event-count" class="badge badge-pending">0</span>
                    </div>
                    <div id="calendar-events"><div class="empty-state"><div class="empty-state-icon">📅</div><p>No upcoming events. Connect Google Calendar in Settings to sync.</p></div></div>
                </div>
            </section>

            <section id="section-settings" class="section">
                <div class="page-header">
                    <h1 class="page-title">Settings</h1>
                    <p class="page-subtitle">Configure The Warden's behavior</p>
                </div>
                <div class="grid-2">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">LLM Model<span id="model-count" class="model-count"></span></h3>
                        </div>
                        <select id="model-selector" class="model-select" onchange="selectModel(this.value)">
                            <option value="">Loading models...</option>
                        </select>
                        <div id="model-info" class="model-info" style="display: none;">
                            <div class="model-info-label">Model ID</div>
                            <div id="model-id-display" class="model-info-value"></div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header"><h3 class="card-title">Quick Actions</h3></div>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <button class="btn btn-secondary" onclick="triggerCheckin()">🔔 Trigger Check-in</button>
                            <button class="btn btn-secondary" onclick="triggerWeeklyReview()">📊 Trigger Weekly Review</button>
                        </div>
                    </div>
                </div>

                <!-- Check-in Schedules Section -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">🕐 Check-in Schedules</h3>
                        <button class="btn btn-sm btn-primary" onclick="showAddScheduleForm()">+ Add Schedule</button>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                        Configure when The Warden checks in with you. Add multiple schedules for different times.
                    </p>
                    <div id="schedules-list"><div class="empty-state">Loading schedules...</div></div>
                    <div id="add-schedule-form" style="display: none; margin-top: 16px; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                        <h4 id="schedule-form-title" style="margin-bottom: 12px;">Add New Schedule</h4>
                        <div class="grid-2" style="margin-bottom: 12px;">
                            <div class="form-group" style="margin-bottom: 0;">
                                <label class="form-label">Name</label>
                                <input type="text" id="sched-name" class="form-input" placeholder="e.g., Morning Check-in" />
                            </div>
                            <div class="form-group" style="margin-bottom: 0;">
                                <label class="form-label">Type</label>
                                <select id="sched-type" class="form-input">
                                    <option value="daily_checkin">Morning Check-in</option>
                                    <option value="custom_reminder">Custom Reminder</option>
                                    <option value="weekly_review">Weekly Review</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid-2" style="margin-bottom: 12px;">
                            <div class="form-group" style="margin-bottom: 0;">
                                <label class="form-label">Time</label>
                                <input type="time" id="sched-time" class="form-input" value="09:00" />
                            </div>
                            <div class="form-group" style="margin-bottom: 0;">
                                <label class="form-label">Days (leave blank for every day)</label>
                                <input type="text" id="sched-days" class="form-input" placeholder="mon,tue,wed,thu,fri" />
                            </div>
                        </div>
                        <div class="form-group" style="margin-bottom: 12px;">
                            <label class="form-label">Custom Prompt (optional - leave blank for default)</label>
                            <textarea id="sched-prompt" class="form-textarea" style="min-height: 80px;" placeholder="Custom instructions for this check-in..."></textarea>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button id="schedule-save-btn" class="btn btn-primary" onclick="saveSchedule()">Save Schedule</button>
                            <button class="btn btn-secondary" onclick="hideAddScheduleForm()">Cancel</button>
                        </div>
                    </div>
                </div>

                <!-- Quiet Hours Section -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">🌙 Quiet Hours</h3>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                        During quiet hours, The Warden won't send scheduled messages. Replies to your messages are still allowed.
                    </p>
                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="quiet-hours-enabled" onchange="updateQuietHours()" />
                            <span>Enable Quiet Hours</span>
                            <span id="quiet-status" class="badge badge-pending" style="margin-left: 8px;"></span>
                        </label>
                    </div>
                    <div class="grid-2" style="margin-top: 12px;">
                        <div class="form-group" style="margin-bottom: 0;">
                            <label class="form-label">Start Time (no messages after)</label>
                            <input type="time" id="quiet-start" class="form-input" value="19:30" onchange="updateQuietHours()" />
                        </div>
                        <div class="form-group" style="margin-bottom: 0;">
                            <label class="form-label">End Time (messages resume)</label>
                            <input type="time" id="quiet-end" class="form-input" value="04:00" onchange="updateQuietHours()" />
                        </div>
                    </div>
                </div>

                <!-- Check-in Prompts Section -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">📝 Check-in Prompts</h3>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                        Customize the prompts used for different types of check-ins. These control what The Warden says.
                    </p>
                    <div id="prompts-list"><div class="empty-state">Loading prompts...</div></div>
                    <div id="edit-prompt-form" style="display: none; margin-top: 16px; padding: 16px; background: var(--bg-tertiary); border-radius: 8px;">
                        <h4 style="margin-bottom: 4px;">Edit Prompt: <span id="edit-prompt-type"></span></h4>
                        <p style="color: var(--text-muted); font-size: 12px; margin-bottom: 12px;">This prompt tells the LLM how to generate check-in messages.</p>
                        <div class="form-group" style="margin-bottom: 12px;">
                            <textarea id="edit-prompt-content" class="form-textarea" style="min-height: 150px;"></textarea>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-primary" onclick="savePromptEdit()">Save Prompt</button>
                            <button class="btn btn-secondary" onclick="resetPromptType()">Reset to Default</button>
                            <button class="btn btn-secondary" onclick="hideEditPromptForm()">Cancel</button>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">System Prompt</h3>
                        <button class="btn btn-sm btn-secondary" onclick="resetPrompt()">Reset to Default</button>
                    </div>
                    <div class="form-group"><textarea id="system-prompt" class="form-textarea" style="min-height: 300px;"></textarea></div>
                    <button class="btn btn-primary" onclick="savePrompt()">Save Prompt</button>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Google Calendar Integration</h3>
                        <span id="calendar-status" class="badge badge-pending">Not Connected</span>
                    </div>
                    <p style="color: var(--text-secondary); font-size: 13px; margin-bottom: 16px;">
                        Connect your Google Calendar to enable meeting-aware check-ins and OOO detection.
                    </p>
                    <div id="calendar-config-form">
                        <div class="form-group">
                            <label class="form-label">Client ID</label>
                            <input type="text" id="gcal-client-id" class="form-input" placeholder="your-client-id.apps.googleusercontent.com" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Client Secret</label>
                            <input type="password" id="gcal-client-secret" class="form-input" placeholder="Client secret from Google Cloud Console" />
                        </div>
                        <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                            <button class="btn btn-primary" onclick="startCalendarAuth()">Connect Calendar</button>
                            <button class="btn btn-secondary" onclick="disconnectCalendar()">Disconnect</button>
                        </div>
                        <div id="auth-code-section" style="display: none;">
                            <p style="color: var(--warning); font-size: 13px; margin-bottom: 12px;">
                                After authorizing, paste the code from the redirect URL here:
                            </p>
                            <div class="form-group">
                                <label class="form-label">Authorization Code</label>
                                <input type="text" id="gcal-auth-code" class="form-input" placeholder="Paste the code from the URL" />
                            </div>
                            <button class="btn btn-success" onclick="submitAuthCode()">Submit Code</button>
                        </div>
                    </div>
                    <div style="margin-top: 16px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px; font-size: 12px; color: var(--text-muted);">
                        <strong>Setup instructions:</strong><br>
                        1. Go to <a href="https://console.cloud.google.com" target="_blank" style="color: var(--accent);">Google Cloud Console</a><br>
                        2. Create a project and enable the Google Calendar API<br>
                        3. Go to Credentials → Create OAuth 2.0 Client ID (Web application)<br>
                        4. Add <code style="background: var(--bg-primary); padding: 2px 6px; border-radius: 4px;">${window.location.origin}/api/calendar/callback</code> as an authorized redirect URI<br>
                        5. Copy Client ID and Secret here, then click "Connect Calendar"
                    </div>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <div class="card-header">
                        <h3 class="card-title">Telegram Webhook</h3>
                        <span id="webhook-status" class="badge badge-pending">Unknown</span>
                    </div>
                    <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">
                        The webhook allows The Warden to receive your Telegram replies.
                    </p>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <button class="btn btn-primary" onclick="setupWebhook()">Setup Webhook</button>
                        <button class="btn btn-secondary" onclick="checkWebhookStatus()">Check Status</button>
                    </div>
                    <div id="webhook-info" style="margin-top: 12px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px; font-size: 12px; display: none;">
                        <div id="webhook-details"></div>
                    </div>
                </div>
            </section>

            <section id="section-errors" class="section">
                <div class="page-header">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h1 class="page-title">Error Log</h1>
                            <p class="page-subtitle">Track and resolve application errors</p>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-secondary" onclick="loadErrors()">Refresh</button>
                            <button class="btn btn-success" onclick="resolveAllErrors()">Resolve All</button>
                            <button class="btn btn-danger" onclick="clearResolvedErrors()">Clear Resolved</button>
                        </div>
                    </div>
                </div>

                <div class="metrics-grid" style="grid-template-columns: repeat(4, 1fr);">
                    <div class="metric-card"><div class="metric-label">Total Errors</div><div class="metric-value" id="error-total">--</div></div>
                    <div class="metric-card warning"><div class="metric-label">Unresolved</div><div class="metric-value" id="error-unresolved">--</div></div>
                    <div class="metric-card success"><div class="metric-label">Resolved</div><div class="metric-value" id="error-resolved">--</div></div>
                    <div class="metric-card info"><div class="metric-label">Last 24h</div><div class="metric-value" id="error-recent">--</div></div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Recent Errors</h3>
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary);">
                            <input type="checkbox" id="unresolved-only" onchange="loadErrors()"> Show unresolved only
                        </label>
                    </div>
                    <div id="errors-list"><div class="empty-state">Loading...</div></div>
                </div>

                <!-- Error Detail Modal -->
                <div id="error-detail-modal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center;">
                    <div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 24px; max-width: 800px; width: 90%; max-height: 80vh; overflow-y: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3 id="error-detail-title" style="font-size: 18px;">Error Details</h3>
                            <button class="btn btn-secondary btn-sm" onclick="closeErrorDetail()">✕ Close</button>
                        </div>
                        <div id="error-detail-content"></div>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let API_KEY = localStorage.getItem('warden_api_key') || '';
        let currentCommitmentFilter = 'pending';

        // Mobile sidebar functions
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        }

        function closeSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }

        // Close sidebar when clicking a nav item on mobile
        function showSectionMobile(section) {
            closeSidebar();
            showSection(section);
        }

        if (API_KEY) { document.getElementById('apiKeyInput').value = API_KEY; authenticate(); }

        async function api(method, endpoint, data = null) {
            try {
                const opts = { method, headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' } };
                if (data) opts.body = JSON.stringify(data);
                const res = await fetch('/api' + endpoint, opts);
                if (res.status === 401 || res.status === 403) { showToast('Invalid API key', 'error'); return null; }
                if (!res.ok) {
                    const errorText = await res.text();
                    console.error('API error:', res.status, errorText);
                    showToast('Server error: ' + res.status, 'error');
                    return null;
                }
                return res.status === 204 ? null : await res.json();
            } catch (e) {
                console.error('API fetch error:', e);
                showToast('Connection error', 'error');
                return null;
            }
        }

        function showToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = 'toast show ' + type;
            setTimeout(() => toast.className = 'toast', 3000);
        }

        function showSection(name) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('section-' + name).classList.add('active');
            event.target.closest('.nav-item').classList.add('active');
            if (name === 'dashboard') loadPatterns();
            if (name === 'chat') loadChatHistory();
            if (name === 'commitments') loadCommitments();
            if (name === 'goals') loadGoals();
            if (name === 'calendar') loadCalendarEvents();
            if (name === 'settings') loadSettings();
            if (name === 'errors') loadErrors();
            // Close sidebar on mobile after navigation
            closeSidebar();
        }

        async function authenticate() {
            API_KEY = document.getElementById('apiKeyInput').value;
            localStorage.setItem('warden_api_key', API_KEY);
            const stats = await api('GET', '/checkins/stats');
            if (stats) {
                document.getElementById('auth-overlay').style.display = 'none';
                document.getElementById('app').style.display = 'flex';
                document.getElementById('mobile-header').style.display = '';
                loadDashboard();
            }
        }

        async function loadDashboard() {
            const stats = await api('GET', '/checkins/stats');
            const streaks = await api('GET', '/settings/streaks');

            if (!stats) return;
            document.getElementById('metric-completion').textContent = (stats.completion_rate * 100).toFixed(0) + '%';
            document.getElementById('metric-pending').textContent = stats.pending_commitments;

            // Display streaks
            if (streaks) {
                const respStreak = streaks.response_streak || {};
                const compStreak = streaks.completion_streak || {};

                document.getElementById('metric-response-streak').textContent = respStreak.current || 0;
                document.getElementById('streak-response-best').textContent = respStreak.best > 0 ? `Best: ${respStreak.best} days` : '';

                document.getElementById('metric-completion-streak').textContent = compStreak.current || 0;
                document.getElementById('streak-completion-best').textContent = compStreak.best > 0 ? `Best: ${compStreak.best} weeks` : '';
            }

            // Load patterns separately
            loadPatterns();

            const checkins = await api('GET', '/checkins?limit=5');
            document.getElementById('recent-activity').innerHTML = checkins && checkins.length
                ? checkins.map(c => `<div class="list-item"><div><div class="list-item-title">${c.response_received ? '✅' : '⏳'} ${c.check_in_type.replace('_', ' ')}</div><div class="list-item-meta">${new Date(c.sent_at).toLocaleString()}</div></div></div>`).join('')
                : '<div class="empty-state">No check-ins yet</div>';
        }

        async function loadPatterns() {
            const patterns = await api('GET', '/checkins/patterns');
            const container = document.getElementById('patterns-list');

            if (!patterns || !patterns.length) {
                container.innerHTML = '<div class="empty-state">No patterns detected</div>';
                return;
            }

            // Map severity to emoji and CSS class
            const getSeverityIndicator = (severity) => {
                if (severity >= 4) return { emoji: '🔴', class: '' };
                if (severity >= 2) return { emoji: '🟡', class: 'medium' };
                return { emoji: '🟢', class: 'low' };
            };

            container.innerHTML = patterns.map(p => {
                const indicator = getSeverityIndicator(p.severity);
                return `<div class="pattern-item ${indicator.class}">
                    <div class="pattern-type">${indicator.emoji} ${p.pattern_type.replace('_', ' ').toUpperCase()}</div>
                    <div class="pattern-desc">${p.description}</div>
                </div>`;
            }).join('');
        }

        async function loadChatHistory() {
            const messages = await api('GET', '/settings/chat-history?limit=50');
            const container = document.getElementById('chat-messages');
            if (!messages || !messages.length) { container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">💬</div><p>No messages yet. Say hi!</p></div>'; return; }
            container.innerHTML = messages.map(m => `<div class="chat-message ${m.role}"><div class="chat-avatar">${m.role === 'warden' ? '🔒' : '👤'}</div><div>${m.message_type ? `<div class="chat-type">${m.message_type.replace('_', ' ')}</div>` : ''}<div class="chat-bubble">${m.content}</div><div class="chat-time">${new Date(m.created_at).toLocaleString()}</div></div></div>`).join('');
            container.scrollTop = container.scrollHeight;

            // Load chat history count setting
            const countResult = await api('GET', '/settings/chat-history-count');
            if (countResult) {
                document.getElementById('chat-history-count').value = countResult.count;
            }

            // Load memory
            await loadMemory();
        }

        async function sendChatMessage(event) {
            event.preventDefault();

            const input = document.getElementById('chat-input');
            const sendBtn = document.getElementById('chat-send-btn');
            const message = input.value.trim();

            if (!message) return;

            // Disable input while sending
            input.disabled = true;
            sendBtn.disabled = true;
            sendBtn.classList.add('loading');

            // Immediately add user message to chat
            const container = document.getElementById('chat-messages');
            const userMsgHtml = `<div class="chat-message user"><div class="chat-avatar">👤</div><div><div class="chat-bubble">${escapeHtml(message)}</div><div class="chat-time">${new Date().toLocaleString()}</div></div></div>`;
            container.insertAdjacentHTML('beforeend', userMsgHtml);
            container.scrollTop = container.scrollHeight;

            // Clear input
            input.value = '';

            try {
                // Send message to API
                const response = await api('POST', '/settings/chat/send', { message });

                if (response && response.reply) {
                    // Add Warden's reply to chat
                    const wardenMsgHtml = `<div class="chat-message warden"><div class="chat-avatar">🔒</div><div><div class="chat-type">reply</div><div class="chat-bubble">${escapeHtml(response.reply)}</div><div class="chat-time">${new Date().toLocaleString()}</div></div></div>`;
                    container.insertAdjacentHTML('beforeend', wardenMsgHtml);
                    container.scrollTop = container.scrollHeight;
                } else {
                    showToast('Failed to get response', 'error');
                }
            } catch (error) {
                console.error('Chat error:', error);
                showToast('Failed to send message', 'error');
            } finally {
                // Re-enable input
                input.disabled = false;
                sendBtn.disabled = false;
                sendBtn.classList.remove('loading');
                input.focus();
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function loadMemory() {
            const result = await api('GET', '/settings/memory');
            if (result) {
                document.getElementById('llm-memory').value = result.memory || '';
            }
        }

        function toggleMemoryPanel() {
            const panel = document.getElementById('memory-panel');
            const icon = document.getElementById('memory-toggle-icon');
            if (panel.style.display === 'none') {
                panel.style.display = 'block';
                icon.textContent = '▲';
            } else {
                panel.style.display = 'none';
                icon.textContent = '▼';
            }
        }

        async function saveMemory() {
            const memory = document.getElementById('llm-memory').value;
            const result = await api('PUT', '/settings/memory', { value: memory });
            if (result) {
                showToast('Memory saved');
            }
        }

        async function clearMemory() {
            if (!confirm('Clear all of Warden\\'s memory? This cannot be undone.')) return;
            const result = await api('DELETE', '/settings/memory');
            if (result) {
                document.getElementById('llm-memory').value = '';
                showToast('Memory cleared');
            }
        }

        // Agent Intelligence Functions
        function toggleAgentPanel() {
            const panel = document.getElementById('agent-panel');
            const icon = document.getElementById('agent-toggle-icon');
            if (panel.style.display === 'none') {
                panel.style.display = 'block';
                icon.textContent = '▲';
                loadAgentData();
            } else {
                panel.style.display = 'none';
                icon.textContent = '▼';
            }
        }

        async function loadAgentData() {
            // Load intensity
            const intensityResult = await api('GET', '/settings/agent/intensity');
            if (intensityResult) {
                const intensity = intensityResult.intensity || 3;
                document.getElementById('intensity-slider').value = intensity;
                updateIntensityLabel(intensity);
            }

            // Load thinking level
            const thinkingResult = await api('GET', '/settings/agent/thinking-level');
            if (thinkingResult) {
                const level = thinkingResult.thinking_level || 'medium';
                document.getElementById('thinking-level').value = level;
                updateThinkingCostLabel(level);
            }

            // Load mood trend
            const moodResult = await api('GET', '/settings/agent/mood?days=7');
            if (moodResult) {
                const avgMood = moodResult.avg_mood;
                const avgEnergy = moodResult.avg_energy;
                document.getElementById('avg-mood-value').textContent = avgMood ? avgMood.toFixed(1) : '--';
                document.getElementById('avg-energy-value').textContent = avgEnergy ? avgEnergy.toFixed(1) : '--';

                // Set mood icon based on average
                const moodIcons = ['😢', '😕', '😐', '🙂', '😄'];
                if (avgMood) {
                    document.getElementById('avg-mood-icon').textContent = moodIcons[Math.round(avgMood) - 1] || '😐';
                }
            }

            // Load follow-ups
            const followupsResult = await api('GET', '/settings/agent/followups');
            if (followupsResult && followupsResult.followups) {
                const container = document.getElementById('followups-list');
                if (followupsResult.followups.length === 0) {
                    container.innerHTML = '<div class="empty-state" style="padding: 16px; font-size: 13px;">No scheduled follow-ups</div>';
                } else {
                    container.innerHTML = followupsResult.followups.map(f => {
                        const scheduledDate = new Date(f.scheduled_time);
                        const dateStr = scheduledDate.toLocaleDateString();
                        const timeStr = scheduledDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                        return `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 8px;">
                                <div>
                                    <div style="font-weight: 500;">${f.topic}</div>
                                    <div style="font-size: 12px; color: var(--text-muted);">📅 ${dateStr} ${timeStr}</div>
                                </div>
                                <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="cancelFollowup(${f.id})">Cancel</button>
                            </div>
                        `;
                    }).join('');
                }
            }
        }

        function updateIntensityLabel(value) {
            const labels = {1: 'Gentle (1)', 2: 'Supportive (2)', 3: 'Balanced (3)', 4: 'Firm (4)', 5: 'Intense (5)'};
            document.getElementById('intensity-label').textContent = labels[value] || 'Balanced (3)';
        }

        async function updateIntensity(value) {
            updateIntensityLabel(value);
            const result = await api('PUT', `/settings/agent/intensity?intensity=${value}`);
            if (result) {
                showToast(`Intensity set to ${value}`);
            }
        }

        function updateThinkingCostLabel(level) {
            const costs = {
                'off': '💨 Fastest, cheapest',
                'minimal': '💰 Very low cost',
                'low': '💰 Low cost',
                'medium': '💰💰 Moderate cost',
                'high': '💰💰💰 Higher cost, best reasoning'
            };
            document.getElementById('thinking-cost').textContent = costs[level] || '💰💰 Moderate cost';
        }

        async function updateThinkingLevel(level) {
            updateThinkingCostLabel(level);
            const result = await api('PUT', `/settings/agent/thinking-level?level=${level}`);
            if (result) {
                showToast(`Thinking level set to ${level}`);
            }
        }

        async function cancelFollowup(id) {
            if (!confirm('Cancel this follow-up?')) return;
            const result = await api('DELETE', `/settings/agent/followups/${id}`);
            if (result) {
                showToast('Follow-up cancelled');
                loadAgentData();
            }
        }

        async function updateChatHistoryCount(count) {
            const result = await api('PUT', `/settings/chat-history-count?count=${count}`);
            if (result) {
                showToast(`LLM will now see last ${count} messages`);
            }
        }

        async function loadCommitments() {
            const commits = await api('GET', `/commitments?status_filter=${currentCommitmentFilter}&limit=50`);
            const container = document.getElementById('commitments-list');
            if (!commits || !commits.length) { container.innerHTML = '<div class="empty-state">No commitments found</div>'; return; }
            container.innerHTML = commits.map(c => {
                const dueDate = c.due_date ? new Date(c.due_date) : null;
                const dateStr = dueDate ? dueDate.toLocaleDateString() : '';
                const timeStr = dueDate ? dueDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '';
                const dueDisplay = dueDate ? `📅 ${dateStr} at ${timeStr}` : '';
                const deferredBadge = c.deferred_count > 0 ? `<span style="color: var(--warning);">🔄 Deferred ${c.deferred_count}x</span>` : '';

                if (c.status === 'pending') {
                    return `<div class="list-item">
                        <div style="flex: 1;">
                            <div class="list-item-title">${c.title}</div>
                            <div class="list-item-meta">${dueDisplay} ${deferredBadge}</div>
                        </div>
                        <div class="list-item-actions" style="display: flex; gap: 8px; align-items: center;">
                            <button class="btn btn-sm btn-secondary" onclick="editCommitmentTime(${c.id}, '${c.title}', '${c.due_date || ''}')">📅</button>
                            <button class="btn btn-sm btn-success" onclick="completeCommitment(${c.id})">✓</button>
                            <button class="btn btn-sm btn-warning" onclick="deferCommitment(${c.id})">Defer</button>
                        </div>
                    </div>`;
                } else {
                    return `<div class="list-item">
                        <div><div class="list-item-title">${c.title}</div><div class="list-item-meta">${dueDisplay} ${deferredBadge}</div></div>
                        <div class="list-item-actions"><span class="badge badge-${c.status}">${c.status}</span></div>
                    </div>`;
                }
            }).join('');
        }

        function filterCommitments(status) {
            currentCommitmentFilter = status;
            document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            loadCommitments();
        }

        async function createCommitment(e) {
            e.preventDefault();
            const data = { title: document.getElementById('commit-title').value };
            const due = document.getElementById('commit-due').value;
            const time = document.getElementById('commit-time').value || '12:00';
            if (due) data.due_date = due + 'T' + time + ':00';
            if (await api('POST', '/commitments', data)) {
                showToast('Commitment added');
                document.getElementById('commit-title').value = '';
                document.getElementById('commit-due').value = '';
                document.getElementById('commit-time').value = '12:00';
                loadCommitments();
                loadDashboard();
            }
        }

        async function editCommitmentTime(id, title, currentDueDate) {
            const dueDate = currentDueDate ? new Date(currentDueDate) : new Date();
            const dateVal = dueDate.toISOString().split('T')[0];
            const timeVal = dueDate.toTimeString().slice(0, 5);

            const newDate = prompt(`Edit due date for "${title}" (YYYY-MM-DD):`, dateVal);
            if (!newDate) return;

            const newTime = prompt(`Edit due time (HH:MM):`, timeVal);
            if (!newTime) return;

            const newDueDate = newDate + 'T' + newTime + ':00';
            if (await api('PUT', `/commitments/${id}`, { due_date: newDueDate })) {
                showToast('Due date updated');
                loadCommitments();
            }
        }

        async function completeCommitment(id) { await api('POST', `/commitments/${id}/complete`); showToast('Marked complete'); loadCommitments(); loadDashboard(); }
        async function deferCommitment(id) { await api('POST', `/commitments/${id}/defer`); showToast('Deferred'); loadCommitments(); }

        async function loadGoals() {
            const goals = await api('GET', '/goals');
            const container = document.getElementById('goals-list');
            if (!goals || !goals.length) { container.innerHTML = '<div class="empty-state">No goals set</div>'; return; }
            container.innerHTML = goals.map(g => `<div class="list-item"><div><div class="list-item-title">${g.title}</div><div class="list-item-meta">${g.description || ''} ${g.target_date ? '📅 ' + new Date(g.target_date).toLocaleDateString() : ''}</div></div><div class="list-item-actions"><button class="btn btn-sm btn-danger" onclick="deleteGoal(${g.id})">🗑️</button></div></div>`).join('');
        }

        async function createGoal(e) {
            e.preventDefault();
            const data = { title: document.getElementById('goal-title').value };
            const desc = document.getElementById('goal-desc').value;
            const date = document.getElementById('goal-date').value;
            if (desc) data.description = desc;
            if (date) data.target_date = date + 'T00:00:00';
            if (await api('POST', '/goals', data)) { showToast('Goal added'); document.getElementById('goal-title').value = ''; document.getElementById('goal-desc').value = ''; document.getElementById('goal-date').value = ''; loadGoals(); }
        }

        async function deleteGoal(id) { if (!confirm('Delete this goal?')) return; await api('DELETE', `/goals/${id}`); showToast('Goal deleted'); loadGoals(); }

        async function loadCalendarEvents() {
            // Load commitments for calendar view
            const commits = await api('GET', '/commitments?status_filter=pending&limit=50');
            const commitContainer = document.getElementById('calendar-commitments');
            const commitCountBadge = document.getElementById('commitment-count');

            const upcomingCommits = (commits || []).filter(c => c.due_date);
            if (!upcomingCommits.length) {
                commitContainer.innerHTML = '<div class="empty-state">No pending commitments with deadlines</div>';
                commitCountBadge.textContent = '0';
            } else {
                commitCountBadge.textContent = upcomingCommits.length;

                // Sort by due date
                upcomingCommits.sort((a, b) => new Date(a.due_date) - new Date(b.due_date));

                // Group by date
                const grouped = {};
                upcomingCommits.forEach(c => {
                    const date = new Date(c.due_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                    if (!grouped[date]) grouped[date] = [];
                    grouped[date].push(c);
                });

                let html = '';
                for (const [date, dayCommits] of Object.entries(grouped)) {
                    html += `<div style="margin-bottom: 16px;">
                        <div style="font-weight: 600; color: var(--warning); margin-bottom: 8px; font-size: 13px;">${date}</div>`;
                    dayCommits.forEach(c => {
                        const time = new Date(c.due_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                        const deferred = c.deferred_count > 0 ? ` <span style="color: var(--warning); font-size: 11px;">(deferred ${c.deferred_count}x)</span>` : '';
                        html += `<div class="calendar-event" style="border-left: 3px solid var(--warning);">
                            <div class="event-time">${time}</div>
                            <div>
                                <div class="event-title">📋 ${c.title}${deferred}</div>
                            </div>
                            <div style="margin-left: auto;">
                                <button class="btn btn-sm btn-success" onclick="completeCommitment(${c.id}); loadCalendarEvents();">✓</button>
                            </div>
                        </div>`;
                    });
                    html += '</div>';
                }
                commitContainer.innerHTML = html;
            }

            // Load calendar events
            const events = await api('GET', '/calendar/events?days_ahead=14');
            const container = document.getElementById('calendar-events');
            const countBadge = document.getElementById('event-count');
            const syncStatus = document.getElementById('calendar-sync-status');

            if (!events || !events.length) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📅</div><p>No upcoming events. Connect Google Calendar in Settings to sync.</p></div>';
                countBadge.textContent = '0';
                return;
            }

            countBadge.textContent = events.length;
            syncStatus.textContent = 'Synced';
            syncStatus.className = 'badge badge-completed';

            // Group events by date
            const eventGrouped = {};
            events.forEach(e => {
                const date = new Date(e.start_time).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                if (!eventGrouped[date]) eventGrouped[date] = [];
                eventGrouped[date].push(e);
            });

            let eventsHtml = '';
            for (const [date, dayEvents] of Object.entries(eventGrouped)) {
                eventsHtml += `<div style="margin-bottom: 16px;">
                    <div style="font-weight: 600; color: var(--accent); margin-bottom: 8px; font-size: 13px;">${date}</div>`;
                dayEvents.forEach(e => {
                    const time = e.all_day ? 'All day' : new Date(e.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    eventsHtml += `<div class="calendar-event">
                        <div class="event-time">${time}</div>
                        <div>
                            <div class="event-title">${e.title}</div>
                            ${e.location ? `<div class="event-location">📍 ${e.location}</div>` : ''}
                        </div>
                    </div>`;
                });
                eventsHtml += '</div>';
            }
            container.innerHTML = eventsHtml;
        }

        async function syncCalendar() {
            const syncStatus = document.getElementById('calendar-sync-status');
            syncStatus.textContent = 'Syncing...';
            syncStatus.className = 'badge badge-pending';

            const result = await api('POST', '/calendar/sync');
            if (result && result.status === 'synced') {
                showToast(`Synced ${result.events_synced} events`);
                syncStatus.textContent = 'Synced';
                syncStatus.className = 'badge badge-completed';
                loadCalendarEvents();
            } else {
                showToast('Sync failed. Is Google Calendar connected?', 'error');
                syncStatus.textContent = 'Sync failed';
                syncStatus.className = 'badge badge-overdue';
            }
        }

        let allModels = [];
        let currentModel = '';

        async function loadSettings() {
            const models = await api('GET', '/settings/models');
            const settings = await api('GET', '/settings');

            if (models && settings) {
                allModels = models;
                currentModel = settings.openrouter_model;
                document.getElementById('model-count').textContent = ` (${models.length} available)`;
                renderModelDropdown(models, currentModel);
                document.getElementById('system-prompt').value = settings.system_prompt;

                // Update calendar status
                const calStatus = document.getElementById('calendar-status');
                if (settings.google_calendar_connected) {
                    calStatus.textContent = 'Connected';
                    calStatus.className = 'badge badge-completed';
                } else {
                    calStatus.textContent = 'Not Connected';
                    calStatus.className = 'badge badge-pending';
                    // Pre-fill credentials if available from settings
                    if (settings.gcal_client_id) {
                        document.getElementById('gcal-client-id').value = settings.gcal_client_id;
                    }
                    if (settings.gcal_client_secret) {
                        document.getElementById('gcal-client-secret').value = settings.gcal_client_secret;
                    }
                }
            }

            // Load schedules and prompts
            loadSchedules();
            loadPrompts();
            loadQuietHours();
        }

        async function startCalendarAuth() {
            const clientId = document.getElementById('gcal-client-id').value.trim();
            const clientSecret = document.getElementById('gcal-client-secret').value.trim();

            if (!clientId || !clientSecret) {
                showToast('Please enter Client ID and Client Secret', 'error');
                return;
            }

            // Save credentials first
            const saveResult = await api('POST', '/settings/calendar/credentials', {
                client_id: clientId,
                client_secret: clientSecret
            });

            if (!saveResult) {
                showToast('Failed to save credentials', 'error');
                return;
            }

            // Get auth URL and redirect
            const result = await api('GET', '/settings/calendar/auth-url');
            if (result && result.auth_url) {
                // Show the auth code input section
                document.getElementById('auth-code-section').style.display = 'block';
                // Open auth URL in new tab
                window.open(result.auth_url, '_blank');
                showToast('Authorize in the new tab, then paste the code here');
            } else {
                showToast('Failed to generate auth URL', 'error');
            }
        }

        async function submitAuthCode() {
            const code = document.getElementById('gcal-auth-code').value.trim();
            if (!code) {
                showToast('Please enter the authorization code', 'error');
                return;
            }

            const result = await api('POST', '/settings/calendar/exchange-code', { code: code });
            if (result && result.status === 'connected') {
                showToast('Calendar connected successfully!');
                document.getElementById('auth-code-section').style.display = 'none';
                document.getElementById('gcal-client-id').value = '';
                document.getElementById('gcal-client-secret').value = '';
                document.getElementById('gcal-auth-code').value = '';
                loadSettings();
            } else {
                showToast('Failed to connect calendar: ' + (result?.error || 'Unknown error'), 'error');
            }
        }

        async function disconnectCalendar() {
            if (!confirm('Disconnect Google Calendar?')) return;
            const result = await api('DELETE', '/settings/calendar/credentials');
            if (result) {
                showToast('Calendar disconnected');
                document.getElementById('auth-code-section').style.display = 'none';
                loadSettings();
            }
        }

        // Quiet Hours Functions
        async function loadQuietHours() {
            const result = await api('GET', '/settings/quiet-hours');
            if (result) {
                document.getElementById('quiet-hours-enabled').checked = result.enabled;

                // Format times for input (HH:MM)
                const startHour = String(result.start_hour).padStart(2, '0');
                const startMin = String(result.start_minute).padStart(2, '0');
                const endHour = String(result.end_hour).padStart(2, '0');
                const endMin = String(result.end_minute).padStart(2, '0');

                document.getElementById('quiet-start').value = `${startHour}:${startMin}`;
                document.getElementById('quiet-end').value = `${endHour}:${endMin}`;

                // Update status badge
                const statusBadge = document.getElementById('quiet-status');
                if (result.currently_quiet) {
                    statusBadge.textContent = 'Active Now';
                    statusBadge.className = 'badge badge-completed';
                } else if (result.enabled) {
                    statusBadge.textContent = 'Enabled';
                    statusBadge.className = 'badge badge-pending';
                } else {
                    statusBadge.textContent = 'Disabled';
                    statusBadge.className = 'badge badge-overdue';
                }
            }
        }

        async function updateQuietHours() {
            const enabled = document.getElementById('quiet-hours-enabled').checked;
            const startTime = document.getElementById('quiet-start').value;
            const endTime = document.getElementById('quiet-end').value;

            if (!startTime || !endTime) return;

            const [startHour, startMin] = startTime.split(':').map(Number);
            const [endHour, endMin] = endTime.split(':').map(Number);

            const params = new URLSearchParams({
                enabled: enabled,
                start_hour: startHour,
                start_minute: startMin,
                end_hour: endHour,
                end_minute: endMin
            });

            const result = await api('PUT', `/settings/quiet-hours?${params.toString()}`);

            if (result) {
                showToast('Quiet hours updated');
                loadQuietHours();  // Refresh to show current status
            } else {
                showToast('Failed to update quiet hours', 'error');
            }
        }

        async function setupWebhook() {
            const statusBadge = document.getElementById('webhook-status');
            statusBadge.textContent = 'Setting up...';
            statusBadge.className = 'badge badge-pending';

            try {
                const res = await fetch('/webhook/setup', { method: 'POST' });
                const result = await res.json();

                if (result.status === 'success') {
                    showToast('Webhook configured successfully!');
                    statusBadge.textContent = 'Active';
                    statusBadge.className = 'badge badge-completed';
                    document.getElementById('webhook-info').style.display = 'block';
                    document.getElementById('webhook-details').innerHTML = `<strong>URL:</strong> ${result.webhook_url}`;
                } else {
                    showToast('Failed to setup webhook: ' + result.error, 'error');
                    statusBadge.textContent = 'Error';
                    statusBadge.className = 'badge badge-overdue';
                }
            } catch (e) {
                showToast('Failed to setup webhook', 'error');
                statusBadge.textContent = 'Error';
                statusBadge.className = 'badge badge-overdue';
            }
        }

        async function checkWebhookStatus() {
            const statusBadge = document.getElementById('webhook-status');
            statusBadge.textContent = 'Checking...';

            try {
                const res = await fetch('/webhook/status');
                const result = await res.json();

                if (result.ok && result.result) {
                    const info = result.result;
                    const hasUrl = info.url && info.url.length > 0;
                    statusBadge.textContent = hasUrl ? 'Active' : 'Not Set';
                    statusBadge.className = hasUrl ? 'badge badge-completed' : 'badge badge-pending';

                    document.getElementById('webhook-info').style.display = 'block';
                    let details = `<strong>URL:</strong> ${info.url || 'None'}<br>`;
                    details += `<strong>Pending updates:</strong> ${info.pending_update_count || 0}<br>`;
                    if (info.last_error_message) {
                        details += `<strong style="color: var(--danger);">Last error:</strong> ${info.last_error_message}`;
                    }
                    document.getElementById('webhook-details').innerHTML = details;
                } else {
                    statusBadge.textContent = 'Error';
                    statusBadge.className = 'badge badge-overdue';
                }
            } catch (e) {
                showToast('Failed to check webhook status', 'error');
                statusBadge.textContent = 'Error';
                statusBadge.className = 'badge badge-overdue';
            }
        }

        function renderModelDropdown(models, selectedId) {
            const select = document.getElementById('model-selector');

            // Group by provider
            const grouped = {};
            models.forEach(m => {
                if (!grouped[m.provider]) grouped[m.provider] = [];
                grouped[m.provider].push(m);
            });

            // Sort providers alphabetically
            const providers = Object.keys(grouped).sort();

            let html = '<option value="">-- Select a model --</option>';
            providers.forEach(provider => {
                html += `<optgroup label="${provider} (${grouped[provider].length})">`;
                grouped[provider].forEach(m => {
                    const ctxStr = m.context_length ? ` [${Math.round(m.context_length / 1000)}k]` : '';
                    const selected = m.id === selectedId ? ' selected' : '';
                    html += `<option value="${m.id}"${selected}>${m.name}${ctxStr} ${m.cost}</option>`;
                });
                html += '</optgroup>';
            });

            select.innerHTML = html;

            // Update model info display
            updateModelInfo(selectedId);
        }

        function updateModelInfo(modelId) {
            const infoDiv = document.getElementById('model-info');
            const idDisplay = document.getElementById('model-id-display');
            if (modelId) {
                idDisplay.textContent = modelId;
                infoDiv.style.display = 'block';
            } else {
                infoDiv.style.display = 'none';
            }
        }

        async function selectModel(modelId) {
            if (!modelId) return;
            if (await api('PUT', '/settings/model', { value: modelId })) {
                currentModel = modelId;
                updateModelInfo(modelId);
                showToast('Model updated');
            }
        }
        async function savePrompt() { if (await api('PUT', '/settings/prompt', { value: document.getElementById('system-prompt').value })) showToast('Prompt saved'); }
        async function resetPrompt() { const result = await api('POST', '/settings/prompt/reset'); if (result) { document.getElementById('system-prompt').value = result.prompt; showToast('Prompt reset'); } }
        async function triggerCheckin() { await api('POST', '/trigger/checkin'); showToast('Check-in triggered'); setTimeout(loadDashboard, 2000); }
        async function triggerWeeklyReview() { await api('POST', '/trigger/weekly-review'); showToast('Weekly review triggered'); }
        function addManualEvent() { const title = prompt('Event title:'); if (!title) return; const dateStr = prompt('Date (YYYY-MM-DD):'); if (!dateStr) return; api('POST', `/calendar/events/manual?title=${encodeURIComponent(title)}&start_time=${dateStr}T09:00:00`).then(() => { showToast('Event added'); loadCalendarEvents(); }); }

        // ========== Check-in Schedules ==========
        async function loadSchedules() {
            const schedules = await api('GET', '/settings/schedules');
            const container = document.getElementById('schedules-list');

            if (!schedules || !schedules.length) {
                container.innerHTML = '<div class="empty-state">No custom schedules configured. The default morning check-in at 4:15 AM is still active.</div>';
                return;
            }

            container.innerHTML = schedules.map(s => {
                const timeStr = `${String(s.hour).padStart(2, '0')}:${String(s.minute).padStart(2, '0')}`;
                const daysStr = s.days_of_week || 'Every day';
                const statusBadge = s.is_active
                    ? '<span class="badge badge-completed">Active</span>'
                    : '<span class="badge badge-pending">Paused</span>';
                return `<div class="list-item">
                    <div style="flex: 1;">
                        <div class="list-item-title">${s.name} ${statusBadge}</div>
                        <div class="list-item-meta">⏰ ${timeStr} • ${daysStr} • Type: ${s.check_in_type}</div>
                        ${s.prompt_template ? '<div class="list-item-meta" style="font-style: italic; margin-top: 4px;">Custom prompt configured</div>' : ''}
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-sm btn-primary" onclick="editSchedule(${s.id}, '${s.name}', ${s.hour}, ${s.minute}, '${s.days_of_week || ''}', '${s.check_in_type}', \`${(s.prompt_template || '').replace(/`/g, '\\`')}\`)">Edit</button>
                        <button class="btn btn-sm btn-secondary" onclick="toggleSchedule(${s.id}, ${!s.is_active})">${s.is_active ? 'Pause' : 'Enable'}</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteSchedule(${s.id})">🗑️</button>
                    </div>
                </div>`;
            }).join('');
        }

        let editingScheduleId = null;

        function showAddScheduleForm() {
            editingScheduleId = null;
            document.getElementById('schedule-form-title').textContent = 'Add New Schedule';
            document.getElementById('schedule-save-btn').textContent = 'Save Schedule';
            document.getElementById('add-schedule-form').style.display = 'block';
        }

        function editSchedule(id, name, hour, minute, days, type, prompt) {
            editingScheduleId = id;
            document.getElementById('schedule-form-title').textContent = 'Edit Schedule';
            document.getElementById('schedule-save-btn').textContent = 'Update Schedule';
            document.getElementById('sched-name').value = name;
            document.getElementById('sched-time').value = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
            document.getElementById('sched-days').value = days || '';
            document.getElementById('sched-type').value = type;
            document.getElementById('sched-prompt').value = prompt || '';
            document.getElementById('add-schedule-form').style.display = 'block';
        }

        function hideAddScheduleForm() {
            editingScheduleId = null;
            document.getElementById('add-schedule-form').style.display = 'none';
            document.getElementById('sched-name').value = '';
            document.getElementById('sched-time').value = '09:00';
            document.getElementById('sched-days').value = '';
            document.getElementById('sched-prompt').value = '';
            document.getElementById('schedule-form-title').textContent = 'Add New Schedule';
            document.getElementById('schedule-save-btn').textContent = 'Save Schedule';
        }

        async function saveSchedule() {
            const name = document.getElementById('sched-name').value.trim();
            const type = document.getElementById('sched-type').value;
            const time = document.getElementById('sched-time').value;
            const days = document.getElementById('sched-days').value.trim() || null;
            const prompt = document.getElementById('sched-prompt').value.trim() || null;

            if (!name) { showToast('Name is required', 'error'); return; }
            if (!time) { showToast('Time is required', 'error'); return; }

            const [hour, minute] = time.split(':').map(Number);

            if (editingScheduleId) {
                // Update existing schedule
                const result = await api('PUT', `/settings/schedules/${editingScheduleId}`, {
                    name: name,
                    hour: hour,
                    minute: minute,
                    days_of_week: days,
                    prompt_template: prompt
                });

                if (result) {
                    showToast('Schedule updated');
                    hideAddScheduleForm();
                    loadSchedules();
                }
            } else {
                // Create new schedule
                const result = await api('POST', '/settings/schedules', {
                    name: name,
                    check_in_type: type,
                    hour: hour,
                    minute: minute,
                    days_of_week: days,
                    prompt_template: prompt,
                    is_active: true
                });

                if (result) {
                    showToast('Schedule created');
                    hideAddScheduleForm();
                    loadSchedules();
                }
            }
        }

        async function toggleSchedule(id, active) {
            const result = await api('PUT', `/settings/schedules/${id}`, { is_active: active });
            if (result) {
                showToast(active ? 'Schedule enabled' : 'Schedule paused');
                loadSchedules();
            }
        }

        async function deleteSchedule(id) {
            if (!confirm('Delete this schedule?')) return;
            const result = await api('DELETE', `/settings/schedules/${id}`);
            if (result) {
                showToast('Schedule deleted');
                loadSchedules();
            }
        }

        // ========== Check-in Prompts ==========
        let currentEditingPromptType = null;

        async function loadPrompts() {
            const prompts = await api('GET', '/settings/prompts');
            const container = document.getElementById('prompts-list');

            if (!prompts || !prompts.length) {
                container.innerHTML = '<div class="empty-state">No prompts found</div>';
                return;
            }

            const typeLabels = {
                'daily_checkin': 'Morning Check-in',
                'weekly_review': 'Weekly Review',
                'escalation': 'Escalation',
                'deadline_alert': 'Deadline Alert',
                'custom_reminder': 'Custom Reminder'
            };

            container.innerHTML = prompts.map(p => {
                const label = typeLabels[p.prompt_type] || p.prompt_type;
                const customBadge = p.is_custom
                    ? '<span class="badge badge-completed" style="margin-left: 8px;">Custom</span>'
                    : '<span class="badge badge-pending" style="margin-left: 8px;">Default</span>';
                const preview = p.prompt_template.substring(0, 100) + (p.prompt_template.length > 100 ? '...' : '');
                return `<div class="list-item">
                    <div style="flex: 1;">
                        <div class="list-item-title">${label} ${customBadge}</div>
                        <div class="list-item-meta" style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">${preview}</div>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-sm btn-secondary" onclick="editPrompt('${p.prompt_type}')">Edit</button>
                    </div>
                </div>`;
            }).join('');
        }

        async function editPrompt(promptType) {
            const result = await api('GET', `/settings/prompts/${promptType}`);
            if (!result) return;

            currentEditingPromptType = promptType;

            const typeLabels = {
                'daily_checkin': 'Morning Check-in',
                'weekly_review': 'Weekly Review',
                'escalation': 'Escalation',
                'deadline_alert': 'Deadline Alert',
                'custom_reminder': 'Custom Reminder'
            };

            document.getElementById('edit-prompt-type').textContent = typeLabels[promptType] || promptType;
            document.getElementById('edit-prompt-content').value = result.prompt_template;
            document.getElementById('edit-prompt-form').style.display = 'block';
        }

        function hideEditPromptForm() {
            document.getElementById('edit-prompt-form').style.display = 'none';
            currentEditingPromptType = null;
        }

        async function savePromptEdit() {
            if (!currentEditingPromptType) return;

            const content = document.getElementById('edit-prompt-content').value.trim();
            if (!content) { showToast('Prompt cannot be empty', 'error'); return; }

            const result = await api('PUT', `/settings/prompts/${currentEditingPromptType}`, {
                prompt_template: content
            });

            if (result) {
                showToast('Prompt saved');
                hideEditPromptForm();
                loadPrompts();
            }
        }

        async function resetPromptType() {
            if (!currentEditingPromptType) return;
            if (!confirm('Reset this prompt to default?')) return;

            const result = await api('POST', `/settings/prompts/${currentEditingPromptType}/reset`);
            if (result) {
                showToast('Prompt reset to default');
                document.getElementById('edit-prompt-content').value = result.prompt_template;
                loadPrompts();
            }
        }

        // Listen for auth code from popup window
        window.addEventListener('message', async function(event) {
            if (event.data && event.data.type === 'google-auth-code' && event.data.code) {
                document.getElementById('gcal-auth-code').value = event.data.code;
                document.getElementById('auth-code-section').style.display = 'block';
                showToast('Authorization code received! Click Submit to complete.');
            }
        });

        // ========== Error Log Functions ==========
        async function loadErrors() {
            const unresolvedOnly = document.getElementById('unresolved-only').checked;
            const errors = await api('GET', `/errors?limit=50&unresolved_only=${unresolvedOnly}`);
            const stats = await api('GET', '/errors/stats');

            // Update stats
            if (stats) {
                document.getElementById('error-total').textContent = stats.total_errors;
                document.getElementById('error-unresolved').textContent = stats.unresolved_count;
                document.getElementById('error-resolved').textContent = stats.resolved_count;
                document.getElementById('error-recent').textContent = stats.errors_last_24h;

                // Update badge in nav
                const badge = document.getElementById('error-count-badge');
                if (stats.unresolved_count > 0) {
                    badge.textContent = stats.unresolved_count;
                    badge.style.display = 'inline-flex';
                    badge.className = 'badge badge-failed';
                } else {
                    badge.style.display = 'none';
                }
            }

            const container = document.getElementById('errors-list');
            if (!errors || !errors.length) {
                container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✅</div><p>No errors found. System is running smoothly!</p></div>';
                return;
            }

            container.innerHTML = errors.map(e => {
                const statusBadge = e.resolved
                    ? '<span class="badge badge-completed">Resolved</span>'
                    : '<span class="badge badge-failed">Unresolved</span>';
                const sourceBadge = e.source ? `<span class="badge badge-pending" style="margin-left: 4px;">${e.source}</span>` : '';
                const date = new Date(e.created_at).toLocaleString();

                return `<div class="list-item" style="border-left: 3px solid ${e.resolved ? 'var(--success)' : 'var(--danger)'};">
                    <div style="flex: 1; min-width: 0;">
                        <div class="list-item-title" style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            <span style="color: var(--danger); font-family: 'JetBrains Mono', monospace;">${e.error_type}</span>
                            ${statusBadge}
                            ${sourceBadge}
                        </div>
                        <div class="list-item-meta" style="margin-top: 4px; word-break: break-word;">${e.error_message}</div>
                        <div class="list-item-meta" style="margin-top: 4px; font-size: 11px;">📅 ${date}</div>
                    </div>
                    <div class="list-item-actions" style="flex-shrink: 0;">
                        <button class="btn btn-sm btn-secondary" onclick="viewErrorDetail(${e.id})">Details</button>
                        ${!e.resolved ? `<button class="btn btn-sm btn-success" onclick="resolveError(${e.id})">Resolve</button>` : ''}
                        <button class="btn btn-sm btn-danger" onclick="deleteError(${e.id})">🗑️</button>
                    </div>
                </div>`;
            }).join('');
        }

        async function loadErrorStats() {
            const stats = await api('GET', '/errors/stats');
            if (stats) {
                const badge = document.getElementById('error-count-badge');
                if (stats.unresolved_count > 0) {
                    badge.textContent = stats.unresolved_count;
                    badge.style.display = 'inline-flex';
                    badge.className = 'badge badge-failed';
                } else {
                    badge.style.display = 'none';
                }
            }
        }

        async function viewErrorDetail(id) {
            const error = await api('GET', `/errors/${id}`);
            if (!error) return;

            const modal = document.getElementById('error-detail-modal');
            const content = document.getElementById('error-detail-content');
            const title = document.getElementById('error-detail-title');

            title.textContent = `${error.error_type} - ${new Date(error.created_at).toLocaleString()}`;

            let html = `
                <div style="margin-bottom: 16px;">
                    <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-secondary);">Error Message</div>
                    <div style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--danger);">${error.error_message}</div>
                </div>
            `;

            if (error.user_message) {
                html += `
                    <div style="margin-bottom: 16px;">
                        <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-secondary);">User Message (Trigger)</div>
                        <div style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; font-size: 13px;">${error.user_message}</div>
                    </div>
                `;
            }

            if (error.stack_trace) {
                html += `
                    <div style="margin-bottom: 16px;">
                        <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-secondary);">Stack Trace</div>
                        <pre style="background: var(--bg-primary); padding: 12px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 11px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; max-height: 300px; overflow-y: auto;">${error.stack_trace}</pre>
                    </div>
                `;
            }

            if (error.context) {
                html += `
                    <div style="margin-bottom: 16px;">
                        <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-secondary);">Context</div>
                        <pre style="background: var(--bg-tertiary); padding: 12px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 12px;">${error.context}</pre>
                    </div>
                `;
            }

            html += `
                <div style="display: flex; gap: 8px; margin-top: 16px;">
                    ${!error.resolved ? `<button class="btn btn-success" onclick="resolveError(${error.id}); closeErrorDetail();">Mark Resolved</button>` : '<span class="badge badge-completed" style="padding: 10px 16px;">✓ Resolved</span>'}
                    <button class="btn btn-danger" onclick="deleteError(${error.id}); closeErrorDetail();">Delete</button>
                </div>
            `;

            content.innerHTML = html;
            modal.style.display = 'flex';
        }

        function closeErrorDetail() {
            document.getElementById('error-detail-modal').style.display = 'none';
        }

        async function resolveError(id) {
            const result = await api('POST', `/errors/${id}/resolve`);
            if (result) {
                showToast('Error marked as resolved');
                loadErrors();
            }
        }

        async function resolveAllErrors() {
            if (!confirm('Mark all errors as resolved?')) return;
            const result = await api('POST', '/errors/resolve-all');
            if (result) {
                showToast(`Resolved ${result.count} errors`);
                loadErrors();
            }
        }

        async function deleteError(id) {
            if (!confirm('Delete this error log?')) return;
            const result = await api('DELETE', `/errors/${id}`);
            if (result) {
                showToast('Error deleted');
                loadErrors();
            }
        }

        async function clearResolvedErrors() {
            if (!confirm('Delete all resolved error logs?')) return;
            const result = await api('DELETE', '/errors');
            if (result) {
                showToast(`Cleared ${result.count} resolved errors`);
                loadErrors();
            }
        }

        // Load error count on page load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(loadErrorStats, 1000);
        });
    </script>
</body>
</html>
"""
