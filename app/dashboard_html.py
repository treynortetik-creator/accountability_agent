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

        @media (max-width: 768px) {
            .sidebar { display: none; }
            .main-content { margin-left: 0; padding: 20px; }
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

    <div class="app-container" id="app" style="display: none;">
        <aside class="sidebar">
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
                        <button class="btn btn-secondary" onclick="loadChatHistory()">Refresh</button>
                    </div>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-messages"><div class="empty-state">Loading...</div></div>
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
                            <div class="form-group"><label class="form-label">Due Date</label><input type="date" id="commit-due" class="form-input" /></div>
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
                    <p class="page-subtitle">Upcoming events and deadlines - synced from Google Calendar</p>
                </div>
                <div class="card" style="margin-bottom: 16px;">
                    <div class="card-header">
                        <h3 class="card-title">Calendar Status</h3>
                        <span id="calendar-sync-status" class="badge badge-pending">Not synced</span>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <button class="btn btn-primary" onclick="syncCalendar()">Sync Now</button>
                        <button class="btn btn-secondary" onclick="addManualEvent()">+ Manual Event</button>
                        <span id="last-sync-info" style="color: var(--text-muted); font-size: 13px;"></span>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Upcoming Events (14 days)</h3>
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
        </main>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let API_KEY = localStorage.getItem('warden_api_key') || '';
        let currentCommitmentFilter = 'pending';

        if (API_KEY) { document.getElementById('apiKeyInput').value = API_KEY; authenticate(); }

        async function api(method, endpoint, data = null) {
            const opts = { method, headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' } };
            if (data) opts.body = JSON.stringify(data);
            const res = await fetch('/api' + endpoint, opts);
            if (res.status === 401 || res.status === 403) { showToast('Invalid API key', 'error'); return null; }
            if (!res.ok) return null;
            return res.status === 204 ? null : await res.json();
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
            if (name === 'chat') loadChatHistory();
            if (name === 'commitments') loadCommitments();
            if (name === 'goals') loadGoals();
            if (name === 'calendar') loadCalendarEvents();
            if (name === 'settings') loadSettings();
        }

        async function authenticate() {
            API_KEY = document.getElementById('apiKeyInput').value;
            localStorage.setItem('warden_api_key', API_KEY);
            const stats = await api('GET', '/checkins/stats');
            if (stats) {
                document.getElementById('auth-overlay').style.display = 'none';
                document.getElementById('app').style.display = 'flex';
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

            document.getElementById('patterns-list').innerHTML = stats.active_patterns.length
                ? stats.active_patterns.map(p => `<div class="pattern-item ${p.severity >= 4 ? '' : p.severity >= 2 ? 'medium' : 'low'}"><div class="pattern-type">${p.pattern_type}</div><div class="pattern-desc">${p.description}</div></div>`).join('')
                : '<div class="empty-state">No patterns detected</div>';

            const checkins = await api('GET', '/checkins?limit=5');
            document.getElementById('recent-activity').innerHTML = checkins && checkins.length
                ? checkins.map(c => `<div class="list-item"><div><div class="list-item-title">${c.response_received ? '✅' : '⏳'} ${c.check_in_type.replace('_', ' ')}</div><div class="list-item-meta">${new Date(c.sent_at).toLocaleString()}</div></div></div>`).join('')
                : '<div class="empty-state">No check-ins yet</div>';
        }

        async function loadChatHistory() {
            const messages = await api('GET', '/settings/chat-history?limit=50');
            const container = document.getElementById('chat-messages');
            if (!messages || !messages.length) { container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">💬</div><p>No messages yet</p></div>'; return; }
            container.innerHTML = messages.map(m => `<div class="chat-message ${m.role}"><div class="chat-avatar">${m.role === 'warden' ? '🔒' : '👤'}</div><div>${m.message_type ? `<div class="chat-type">${m.message_type.replace('_', ' ')}</div>` : ''}<div class="chat-bubble">${m.content}</div><div class="chat-time">${new Date(m.created_at).toLocaleString()}</div></div></div>`).join('');
            container.scrollTop = container.scrollHeight;
        }

        async function loadCommitments() {
            const commits = await api('GET', `/commitments?status_filter=${currentCommitmentFilter}&limit=50`);
            const container = document.getElementById('commitments-list');
            if (!commits || !commits.length) { container.innerHTML = '<div class="empty-state">No commitments found</div>'; return; }
            container.innerHTML = commits.map(c => `<div class="list-item"><div><div class="list-item-title">${c.title}</div><div class="list-item-meta">${c.due_date ? '📅 ' + new Date(c.due_date).toLocaleDateString() : ''} ${c.deferred_count > 0 ? '<span style="color: var(--warning);">🔄 Deferred ' + c.deferred_count + 'x</span>' : ''}</div></div><div class="list-item-actions">${c.status === 'pending' ? `<button class="btn btn-sm btn-success" onclick="completeCommitment(${c.id})">✓</button><button class="btn btn-sm btn-warning" onclick="deferCommitment(${c.id})">Defer</button>` : `<span class="badge badge-${c.status}">${c.status}</span>`}</div></div>`).join('');
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
            if (due) data.due_date = due + 'T23:59:59';
            if (await api('POST', '/commitments', data)) { showToast('Commitment added'); document.getElementById('commit-title').value = ''; document.getElementById('commit-due').value = ''; loadCommitments(); loadDashboard(); }
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
            const grouped = {};
            events.forEach(e => {
                const date = new Date(e.start_time).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                if (!grouped[date]) grouped[date] = [];
                grouped[date].push(e);
            });

            let html = '';
            for (const [date, dayEvents] of Object.entries(grouped)) {
                html += `<div style="margin-bottom: 16px;">
                    <div style="font-weight: 600; color: var(--accent); margin-bottom: 8px; font-size: 13px;">${date}</div>`;
                dayEvents.forEach(e => {
                    const time = e.all_day ? 'All day' : new Date(e.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    html += `<div class="calendar-event">
                        <div class="event-time">${time}</div>
                        <div>
                            <div class="event-title">${e.title}</div>
                            ${e.location ? `<div class="event-location">📍 ${e.location}</div>` : ''}
                        </div>
                    </div>`;
                });
                html += '</div>';
            }
            container.innerHTML = html;
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
                }
            }
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

        // Listen for auth code from popup window
        window.addEventListener('message', async function(event) {
            if (event.data && event.data.type === 'google-auth-code' && event.data.code) {
                document.getElementById('gcal-auth-code').value = event.data.code;
                document.getElementById('auth-code-section').style.display = 'block';
                showToast('Authorization code received! Click Submit to complete.');
            }
        });
    </script>
</body>
</html>
"""
