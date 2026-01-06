"""Login page HTML for The Warden."""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - The Warden</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --void: #0a0a0c;
            --obsidian: #0f1115;
            --steel: #1a1d24;
            --chrome: #2a2f3a;
            --neon-pink: #ff2a6d;
            --neon-cyan: #05d9e8;
            --holo-white: #e8f0ff;
            --smoke: #7a8599;
            --danger: #ff0a54;
            --success: #39ff14;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Rajdhani', sans-serif;
            background: var(--void);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--holo-white);
        }

        .login-container {
            background: linear-gradient(135deg, var(--obsidian), var(--steel));
            border: 1px solid var(--chrome);
            border-radius: 16px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .login-logo {
            text-align: center;
            font-size: 3rem;
            margin-bottom: 16px;
        }

        .login-title {
            font-family: 'Orbitron', sans-serif;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--neon-cyan);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 3px;
        }

        .login-subtitle {
            text-align: center;
            color: var(--smoke);
            font-size: 0.875rem;
            margin-bottom: 32px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-label {
            display: block;
            font-size: 0.75rem;
            color: var(--smoke);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .form-input {
            width: 100%;
            padding: 12px 16px;
            background: var(--void);
            border: 1px solid var(--chrome);
            border-radius: 8px;
            color: var(--holo-white);
            font-family: 'Share Tech Mono', monospace;
            font-size: 1rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--neon-cyan);
            box-shadow: 0 0 15px rgba(5, 217, 232, 0.2);
        }

        .btn {
            width: 100%;
            padding: 14px 24px;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-pink));
            border: none;
            border-radius: 8px;
            color: var(--void);
            font-family: 'Orbitron', sans-serif;
            font-size: 0.875rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(5, 217, 232, 0.3);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .error-message {
            background: rgba(255, 10, 84, 0.1);
            border: 1px solid var(--danger);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 20px;
            color: var(--danger);
            font-size: 0.875rem;
            display: none;
        }

        .error-message.show {
            display: block;
        }

        .loading {
            display: none;
            text-align: center;
            color: var(--smoke);
            font-size: 0.875rem;
        }

        .loading.show {
            display: block;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading.show {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-logo">&#x1F512;</div>
        <h1 class="login-title">The Warden</h1>
        <p class="login-subtitle">Enter your credentials to continue</p>

        <div id="error-message" class="error-message"></div>

        <form id="login-form" onsubmit="return handleLogin(event)">
            <div class="form-group">
                <label class="form-label" for="password">Password / API Key</label>
                <input
                    type="password"
                    id="password"
                    class="form-input"
                    placeholder="Enter your password"
                    autocomplete="current-password"
                    required
                />
            </div>

            <div id="loading" class="loading">Authenticating...</div>

            <button type="submit" class="btn" id="submit-btn">
                Connect
            </button>
        </form>
    </div>

    <script>
        async function handleLogin(event) {
            event.preventDefault();

            const password = document.getElementById('password').value;
            const errorEl = document.getElementById('error-message');
            const loadingEl = document.getElementById('loading');
            const submitBtn = document.getElementById('submit-btn');

            // Hide any previous error
            errorEl.classList.remove('show');
            loadingEl.classList.add('show');
            submitBtn.disabled = true;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `password=${encodeURIComponent(password)}`,
                });

                if (response.ok) {
                    // Store the password as API key for API calls
                    localStorage.setItem('warden_api_key', password);
                    // Redirect to dashboard
                    window.location.href = '/dashboard';
                } else if (response.status === 429) {
                    const data = await response.json();
                    errorEl.textContent = data.detail || 'Too many attempts. Please try again later.';
                    errorEl.classList.add('show');
                } else {
                    errorEl.textContent = 'Invalid password. Please try again.';
                    errorEl.classList.add('show');
                }
            } catch (e) {
                errorEl.textContent = 'Connection error. Please try again.';
                errorEl.classList.add('show');
            } finally {
                loadingEl.classList.remove('show');
                submitBtn.disabled = false;
            }

            return false;
        }

        // Focus password field on load
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('password').focus();
        });
    </script>
</body>
</html>
"""
