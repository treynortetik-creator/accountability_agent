"""HTML Dashboard served directly from FastAPI."""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Warden - Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0e1117;
            color: #fafafa;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #262730;
            margin-bottom: 30px;
        }
        h1 { font-size: 1.8rem; }
        h1 span { color: #ff4b4b; }
        .auth-form { display: flex; gap: 10px; }
        .auth-form input {
            background: #262730;
            border: 1px solid #404040;
            color: #fff;
            padding: 8px 12px;
            border-radius: 6px;
            width: 300px;
        }
        .btn {
            background: #ff4b4b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.2s;
        }
        .btn:hover { background: #ff3333; }
        .btn-secondary { background: #262730; }
        .btn-secondary:hover { background: #363740; }
        .btn-success { background: #00cc00; }
        .btn-warning { background: #ffa500; }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #1e2130;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff4b4b;
        }
        .metric-card h3 { color: #888; font-size: 0.9rem; margin-bottom: 8px; }
        .metric-card .value { font-size: 2rem; font-weight: bold; }
        .metric-card.good { border-left-color: #00cc00; }
        .metric-card.warning { border-left-color: #ffa500; }

        .grid-2 { display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }
        @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }

        .card {
            background: #1e2130;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 {
            font-size: 1.2rem;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #262730;
        }

        .pattern {
            background: #262730;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #ff4b4b;
        }
        .pattern.severity-low { border-left-color: #00cc00; }
        .pattern.severity-med { border-left-color: #ffa500; }
        .pattern-type { font-weight: bold; text-transform: uppercase; font-size: 0.8rem; }

        .commitment {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #262730;
        }
        .commitment:last-child { border-bottom: none; }
        .commitment-title { font-weight: 500; }
        .commitment-meta { color: #888; font-size: 0.85rem; }
        .commitment-actions { display: flex; gap: 8px; }
        .commitment-actions button {
            padding: 6px 12px;
            font-size: 0.8rem;
        }

        .status-pending { color: #ffa500; }
        .status-completed { color: #00cc00; }
        .status-failed { color: #ff4b4b; }

        .checkin {
            padding: 12px 0;
            border-bottom: 1px solid #262730;
        }
        .checkin:last-child { border-bottom: none; }
        .checkin-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .checkin-type { font-weight: 500; }
        .checkin-time { color: #888; font-size: 0.85rem; }
        .checkin-message {
            background: #262730;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.9rem;
            color: #ccc;
        }

        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #888; }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            background: #262730;
            border: 1px solid #404040;
            color: #fff;
            padding: 10px 12px;
            border-radius: 6px;
        }
        .form-group textarea { min-height: 80px; resize: vertical; }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid #262730;
            padding-bottom: 10px;
        }
        .tab {
            background: none;
            border: none;
            color: #888;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 1rem;
            border-radius: 6px;
        }
        .tab:hover { color: #fff; background: #262730; }
        .tab.active { color: #fff; background: #ff4b4b; }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #00cc00;
            color: #000;
            padding: 15px 25px;
            border-radius: 8px;
            font-weight: 500;
            display: none;
            z-index: 1000;
        }
        .toast.error { background: #ff4b4b; color: #fff; }
        .toast.show { display: block; }

        .loading { opacity: 0.5; pointer-events: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 The <span>Warden</span></h1>
            <div class="auth-form">
                <input type="password" id="apiKey" placeholder="Enter API Key" />
                <button class="btn" onclick="authenticate()">Connect</button>
            </div>
        </header>

        <div id="dashboard" style="display: none;">
            <div class="tabs">
                <button class="tab active" onclick="showTab('overview')">📊 Overview</button>
                <button class="tab" onclick="showTab('commitments')">✅ Commitments</button>
                <button class="tab" onclick="showTab('goals')">🎯 Goals</button>
                <button class="tab" onclick="showTab('checkins')">📋 Check-ins</button>
            </div>

            <!-- Overview Tab -->
            <div id="tab-overview" class="tab-content active">
                <div class="metrics" id="metrics">
                    <div class="metric-card"><h3>Completion Rate</h3><div class="value" id="completion-rate">--%</div></div>
                    <div class="metric-card warning"><h3>Pending Tasks</h3><div class="value" id="pending-count">--</div></div>
                    <div class="metric-card"><h3>Response Rate</h3><div class="value" id="response-rate">--%</div></div>
                    <div class="metric-card"><h3>Avg Response</h3><div class="value" id="avg-response">--h</div></div>
                </div>

                <div class="grid-2">
                    <div class="card">
                        <h2>Recent Check-ins</h2>
                        <div id="recent-checkins"><div class="empty-state">Loading...</div></div>
                    </div>
                    <div class="card">
                        <h2>🚨 Active Patterns</h2>
                        <div id="patterns"><div class="empty-state">Loading...</div></div>
                    </div>
                </div>

                <div class="card">
                    <h2>⚡ Quick Actions</h2>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn" onclick="triggerCheckin()">🔔 Trigger Check-in</button>
                        <button class="btn btn-secondary" onclick="triggerWeeklyReview()">📊 Trigger Weekly Review</button>
                    </div>
                </div>
            </div>

            <!-- Commitments Tab -->
            <div id="tab-commitments" class="tab-content">
                <div class="card">
                    <h2>➕ Add Commitment</h2>
                    <form id="commitment-form" onsubmit="createCommitment(event)">
                        <div class="form-group">
                            <label>Title</label>
                            <input type="text" id="commit-title" required placeholder="What are you committing to?">
                        </div>
                        <div class="form-group">
                            <label>Due Date (optional)</label>
                            <input type="date" id="commit-due">
                        </div>
                        <div class="form-group">
                            <label>Goal (optional)</label>
                            <select id="commit-goal"><option value="">-- No Goal --</option></select>
                        </div>
                        <button type="submit" class="btn">Add Commitment</button>
                    </form>
                </div>

                <div class="card">
                    <h2>Pending Commitments</h2>
                    <div id="pending-commitments"><div class="empty-state">Loading...</div></div>
                </div>

                <div class="card">
                    <h2>Completed</h2>
                    <div id="completed-commitments"><div class="empty-state">Loading...</div></div>
                </div>
            </div>

            <!-- Goals Tab -->
            <div id="tab-goals" class="tab-content">
                <div class="card">
                    <h2>➕ Add Goal</h2>
                    <form id="goal-form" onsubmit="createGoal(event)">
                        <div class="form-group">
                            <label>Goal Title</label>
                            <input type="text" id="goal-title" required placeholder="What's the goal?">
                        </div>
                        <div class="form-group">
                            <label>Description (optional)</label>
                            <textarea id="goal-desc" placeholder="More details..."></textarea>
                        </div>
                        <div class="form-group">
                            <label>Target Date (optional)</label>
                            <input type="date" id="goal-date">
                        </div>
                        <button type="submit" class="btn">Add Goal</button>
                    </form>
                </div>

                <div class="card">
                    <h2>Active Goals</h2>
                    <div id="goals-list"><div class="empty-state">Loading...</div></div>
                </div>
            </div>

            <!-- Check-ins Tab -->
            <div id="tab-checkins" class="tab-content">
                <div class="card">
                    <h2>Check-in History</h2>
                    <div id="checkins-list"><div class="empty-state">Loading...</div></div>
                </div>
            </div>
        </div>

        <div id="login-prompt" class="card" style="max-width: 500px; margin: 100px auto; text-align: center;">
            <h2>🔒 Enter API Key</h2>
            <p style="color: #888; margin: 20px 0;">Enter your API key to access the dashboard.</p>
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let API_KEY = localStorage.getItem('warden_api_key') || '';

        if (API_KEY) {
            document.getElementById('apiKey').value = API_KEY;
            authenticate();
        }

        async function api(method, endpoint, data = null) {
            const opts = {
                method,
                headers: {
                    'X-API-Key': API_KEY,
                    'Content-Type': 'application/json'
                }
            };
            if (data) opts.body = JSON.stringify(data);
            const res = await fetch('/api' + endpoint, opts);
            if (res.status === 401 || res.status === 403) {
                showToast('Invalid API key', true);
                return null;
            }
            if (!res.ok) {
                showToast('API Error: ' + res.status, true);
                return null;
            }
            return res.status === 204 ? null : await res.json();
        }

        function showToast(msg, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = 'toast show' + (isError ? ' error' : '');
            setTimeout(() => toast.className = 'toast', 3000);
        }

        function showTab(name) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="showTab('${name}')"]`).classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');
        }

        async function authenticate() {
            API_KEY = document.getElementById('apiKey').value;
            localStorage.setItem('warden_api_key', API_KEY);

            const stats = await api('GET', '/checkins/stats');
            if (stats) {
                document.getElementById('dashboard').style.display = 'block';
                document.getElementById('login-prompt').style.display = 'none';
                loadDashboard();
            }
        }

        async function loadDashboard() {
            await Promise.all([loadStats(), loadPatterns(), loadCheckins(), loadCommitments(), loadGoals()]);
        }

        async function loadStats() {
            const stats = await api('GET', '/checkins/stats');
            if (!stats) return;

            document.getElementById('completion-rate').textContent = (stats.completion_rate * 100).toFixed(0) + '%';
            document.getElementById('pending-count').textContent = stats.pending_commitments;
            document.getElementById('response-rate').textContent = (stats.response_rate * 100).toFixed(0) + '%';
            document.getElementById('avg-response').textContent = stats.average_response_time_hours
                ? stats.average_response_time_hours.toFixed(1) + 'h' : 'N/A';
        }

        async function loadPatterns() {
            const stats = await api('GET', '/checkins/stats');
            const container = document.getElementById('patterns');

            if (!stats || !stats.active_patterns.length) {
                container.innerHTML = '<div class="empty-state">No patterns detected. Stay vigilant.</div>';
                return;
            }

            container.innerHTML = stats.active_patterns.map(p => `
                <div class="pattern ${p.severity >= 4 ? '' : p.severity >= 2 ? 'severity-med' : 'severity-low'}">
                    <div class="pattern-type">${p.severity >= 4 ? '🔴' : p.severity >= 2 ? '🟡' : '🟢'} ${p.pattern_type}</div>
                    <div>${p.description}</div>
                </div>
            `).join('');
        }

        async function loadCheckins() {
            const checkins = await api('GET', '/checkins?limit=5');
            const container = document.getElementById('recent-checkins');
            const fullContainer = document.getElementById('checkins-list');

            if (!checkins || !checkins.length) {
                container.innerHTML = '<div class="empty-state">No check-ins yet.</div>';
                fullContainer.innerHTML = '<div class="empty-state">No check-ins yet.</div>';
                return;
            }

            const render = (list) => list.map(c => `
                <div class="checkin">
                    <div class="checkin-header">
                        <span class="checkin-type">${c.response_received ? '✅' : '⏳'} ${c.check_in_type.replace('_', ' ')}</span>
                        <span class="checkin-time">${new Date(c.sent_at).toLocaleString()}</span>
                    </div>
                    <div class="checkin-message">${c.message_sent}</div>
                </div>
            `).join('');

            container.innerHTML = render(checkins);

            const allCheckins = await api('GET', '/checkins?limit=20');
            if (allCheckins) fullContainer.innerHTML = render(allCheckins);
        }

        async function loadCommitments() {
            const pending = await api('GET', '/commitments?status_filter=pending');
            const completed = await api('GET', '/commitments?status_filter=completed&limit=10');

            const renderCommitment = (c) => `
                <div class="commitment">
                    <div>
                        <div class="commitment-title">${c.title}</div>
                        <div class="commitment-meta">
                            ${c.due_date ? '📅 ' + new Date(c.due_date).toLocaleDateString() : ''}
                            ${c.deferred_count > 0 ? ' 🔄 Deferred ' + c.deferred_count + 'x' : ''}
                        </div>
                    </div>
                    <div class="commitment-actions">
                        ${c.status === 'pending' ? `
                            <button class="btn btn-success" onclick="completeCommitment(${c.id})">✓ Done</button>
                            <button class="btn btn-warning" onclick="deferCommitment(${c.id})">Defer</button>
                        ` : ''}
                    </div>
                </div>
            `;

            document.getElementById('pending-commitments').innerHTML = pending && pending.length
                ? pending.map(renderCommitment).join('')
                : '<div class="empty-state">No pending commitments. Time to commit to something.</div>';

            document.getElementById('completed-commitments').innerHTML = completed && completed.length
                ? completed.map(renderCommitment).join('')
                : '<div class="empty-state">Nothing completed yet.</div>';
        }

        async function loadGoals() {
            const goals = await api('GET', '/goals');
            const container = document.getElementById('goals-list');
            const select = document.getElementById('commit-goal');

            select.innerHTML = '<option value="">-- No Goal --</option>';

            if (!goals || !goals.length) {
                container.innerHTML = '<div class="empty-state">No goals set. What are you working toward?</div>';
                return;
            }

            goals.forEach(g => {
                select.innerHTML += `<option value="${g.id}">${g.title}</option>`;
            });

            container.innerHTML = goals.map(g => `
                <div class="commitment">
                    <div>
                        <div class="commitment-title">${g.title}</div>
                        <div class="commitment-meta">
                            ${g.description || ''}
                            ${g.target_date ? ' 📅 ' + new Date(g.target_date).toLocaleDateString() : ''}
                        </div>
                    </div>
                    <div class="commitment-actions">
                        <button class="btn btn-secondary" onclick="deleteGoal(${g.id})">🗑️</button>
                    </div>
                </div>
            `).join('');
        }

        async function createCommitment(e) {
            e.preventDefault();
            const data = {
                title: document.getElementById('commit-title').value,
            };
            const due = document.getElementById('commit-due').value;
            const goal = document.getElementById('commit-goal').value;
            if (due) data.due_date = due + 'T00:00:00';
            if (goal) data.goal_id = parseInt(goal);

            const result = await api('POST', '/commitments', data);
            if (result) {
                showToast('Commitment added');
                document.getElementById('commit-title').value = '';
                document.getElementById('commit-due').value = '';
                loadCommitments();
                loadStats();
            }
        }

        async function createGoal(e) {
            e.preventDefault();
            const data = {
                title: document.getElementById('goal-title').value,
            };
            const desc = document.getElementById('goal-desc').value;
            const date = document.getElementById('goal-date').value;
            if (desc) data.description = desc;
            if (date) data.target_date = date + 'T00:00:00';

            const result = await api('POST', '/goals', data);
            if (result) {
                showToast('Goal added');
                document.getElementById('goal-title').value = '';
                document.getElementById('goal-desc').value = '';
                document.getElementById('goal-date').value = '';
                loadGoals();
            }
        }

        async function completeCommitment(id) {
            const result = await api('POST', `/commitments/${id}/complete`);
            if (result) {
                showToast('Marked complete');
                loadCommitments();
                loadStats();
            }
        }

        async function deferCommitment(id) {
            const result = await api('POST', `/commitments/${id}/defer`);
            if (result) {
                showToast('Deferred');
                loadCommitments();
            }
        }

        async function deleteGoal(id) {
            if (!confirm('Delete this goal?')) return;
            await api('DELETE', `/goals/${id}`);
            showToast('Goal deleted');
            loadGoals();
        }

        async function triggerCheckin() {
            const result = await fetch('/api/trigger/checkin', {
                method: 'POST',
                headers: { 'X-API-Key': API_KEY }
            });
            if (result.ok) {
                showToast('Check-in triggered!');
                setTimeout(loadCheckins, 2000);
            }
        }

        async function triggerWeeklyReview() {
            const result = await fetch('/api/trigger/weekly-review', {
                method: 'POST',
                headers: { 'X-API-Key': API_KEY }
            });
            if (result.ok) {
                showToast('Weekly review triggered!');
                setTimeout(loadCheckins, 2000);
            }
        }
    </script>
</body>
</html>
"""
