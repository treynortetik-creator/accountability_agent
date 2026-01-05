"""
Dashboard HTML Part 1 - Document Head and CSS
The Warden - Cyberpunk Accountability Dashboard
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Warden</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <style>
/* ==========================================================================
   THE WARDEN - CYBERPUNK UI
   Blade Runner / Neo-Tokyo Aesthetic
   ========================================================================== */

/* --------------------------------------------------------------------------
   FONTS - Google Fonts Import
   -------------------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');

/* --------------------------------------------------------------------------
   CSS CUSTOM PROPERTIES
   -------------------------------------------------------------------------- */
:root {
    /* Void & Structure */
    --void: #0a0a0c;
    --obsidian: #0f1115;
    --steel: #1a1d24;
    --chrome: #2a2f3a;

    /* Neon Accents */
    --neon-pink: #ff2a6d;
    --neon-cyan: #05d9e8;
    --neon-blue: #0ff0fc;
    --neon-purple: #d300c5;

    /* Text */
    --holo-white: #e8f0ff;
    --smoke: #7a8599;
    --ash: #4a5568;

    /* Status */
    --danger: #ff0a54;
    --success: #39ff14;
    --warning: #ffd300;

    /* Glow Intensities */
    --glow-sm: 0 0 5px;
    --glow-md: 0 0 10px;
    --glow-lg: 0 0 20px;
    --glow-xl: 0 0 30px;

    /* Transitions */
    --transition-fast: 0.15s ease;
    --transition-med: 0.3s ease;
    --transition-slow: 0.5s ease;

    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 48px;

    /* Border Radius */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;

    /* Command Rail */
    --rail-width: 64px;
    --rail-width-expanded: 200px;

    /* Top Bar */
    --topbar-height: 48px;

    /* Quick Access */
    --quickbar-height: 56px;
}

/* --------------------------------------------------------------------------
   RESET & BASE
   -------------------------------------------------------------------------- */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 400;
    background: var(--void);
    color: var(--holo-white);
    min-height: 100vh;
    line-height: 1.5;
    overflow-x: hidden;
}

/* --------------------------------------------------------------------------
   TYPOGRAPHY
   -------------------------------------------------------------------------- */
.font-display { font-family: 'Orbitron', sans-serif; }
.font-body { font-family: 'Rajdhani', sans-serif; }
.font-mono { font-family: 'Share Tech Mono', monospace; }

h1, h2, h3, h4, h5, h6 {
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

h1 { font-size: 2rem; }
h2 { font-size: 1.5rem; }
h3 { font-size: 1.25rem; }
h4 { font-size: 1rem; }

/* --------------------------------------------------------------------------
   ANIMATED BACKGROUND LAYERS
   -------------------------------------------------------------------------- */

/* Layer 1: Base gradient with noise */
.bg-base {
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse at 20% 80%, rgba(211, 0, 197, 0.1) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(5, 217, 232, 0.08) 0%, transparent 50%),
        linear-gradient(180deg, var(--void) 0%, var(--obsidian) 100%);
    z-index: -5;
}

/* Layer 2: Perspective grid */
.bg-grid {
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(5, 217, 232, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(5, 217, 232, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    transform: perspective(500px) rotateX(60deg);
    transform-origin: center top;
    z-index: -4;
    opacity: 0.5;
}

/* Layer 3: Rain effect */
.bg-rain {
    position: fixed;
    inset: 0;
    z-index: -3;
    overflow: hidden;
    pointer-events: none;
}

.rain-drop {
    position: absolute;
    width: 1px;
    height: 80px;
    background: linear-gradient(to bottom, transparent, rgba(5, 217, 232, 0.3), transparent);
    animation: rain-fall linear infinite;
    opacity: 0.15;
}

@keyframes rain-fall {
    0% { transform: translateY(-100px); }
    100% { transform: translateY(100vh); }
}

/* Layer 4: Fog/Ambient glow */
.bg-fog {
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse at 0% 100%, rgba(255, 42, 109, 0.08) 0%, transparent 40%),
        radial-gradient(ellipse at 100% 0%, rgba(5, 217, 232, 0.06) 0%, transparent 40%);
    z-index: -2;
    animation: fog-pulse 8s ease-in-out infinite alternate;
}

@keyframes fog-pulse {
    0% { opacity: 0.8; }
    100% { opacity: 1; }
}

/* Layer 5: Scanlines */
.bg-scanlines {
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0, 0, 0, 0.03) 2px,
        rgba(0, 0, 0, 0.03) 4px
    );
    z-index: -1;
    pointer-events: none;
}

/* --------------------------------------------------------------------------
   TOP BAR
   -------------------------------------------------------------------------- */
.top-bar {
    position: fixed;
    top: 0;
    left: var(--rail-width);
    right: 0;
    height: var(--topbar-height);
    background: rgba(15, 17, 21, 0.9);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--chrome);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--space-lg);
    z-index: 100;
}

.top-bar-left {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

.top-bar-logo {
    font-family: 'Orbitron', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.1em;
    color: var(--neon-pink);
    text-shadow: var(--glow-sm) var(--neon-pink);
    cursor: pointer;
    transition: var(--transition-fast);
}

.top-bar-logo:hover {
    text-shadow: var(--glow-md) var(--neon-pink);
    animation: glitch 0.1s linear;
}

@keyframes glitch {
    0% { transform: translate(0); }
    20% { transform: translate(-2px, 1px); }
    40% { transform: translate(2px, -1px); }
    60% { transform: translate(-1px, 2px); }
    80% { transform: translate(1px, -2px); }
    100% { transform: translate(0); }
}

.system-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--smoke);
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: var(--glow-sm) var(--success);
    animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
    0%, 100% { opacity: 1; box-shadow: var(--glow-sm) var(--success); }
    50% { opacity: 0.6; box-shadow: var(--glow-md) var(--success); }
}

.top-bar-right {
    display: flex;
    align-items: center;
    gap: var(--space-lg);
}

.top-bar-time {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.875rem;
    color: var(--smoke);
}

/* --------------------------------------------------------------------------
   COMMAND RAIL (Navigation)
   -------------------------------------------------------------------------- */
.command-rail {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: var(--rail-width);
    background: rgba(15, 17, 21, 0.95);
    backdrop-filter: blur(10px);
    border-right: 1px solid var(--chrome);
    display: flex;
    flex-direction: column;
    z-index: 200;
    transition: width var(--transition-med);
}

.command-rail:hover {
    width: var(--rail-width-expanded);
}

.rail-logo {
    height: var(--topbar-height);
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid var(--chrome);
    font-size: 1.75rem;
    color: var(--neon-pink);
    filter: drop-shadow(0 0 8px var(--neon-pink));
}

.rail-nav {
    flex: 1;
    padding: var(--space-md) 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
}

.rail-item {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    padding: var(--space-md);
    margin: 0 var(--space-sm);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: var(--transition-fast);
    color: var(--smoke);
    text-decoration: none;
    overflow: hidden;
    white-space: nowrap;
}

.rail-item:hover {
    background: rgba(5, 217, 232, 0.1);
    color: var(--neon-cyan);
}

.rail-item.active {
    background: rgba(255, 42, 109, 0.15);
    color: var(--neon-pink);
    box-shadow: inset 3px 0 0 var(--neon-pink);
}

.rail-icon {
    font-size: 1.25rem;
    width: 32px;
    text-align: center;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.rail-icon i {
    font-size: 1.35rem;
    transition: all 0.3s ease;
}

.rail-item.active .rail-icon i {
    color: var(--neon-pink);
    filter: drop-shadow(0 0 6px var(--neon-pink));
}

.rail-item:hover .rail-icon i {
    color: var(--neon-cyan);
    filter: drop-shadow(0 0 4px var(--neon-cyan));
}

.rail-label {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    opacity: 0;
    transition: opacity var(--transition-med);
}

.command-rail:hover .rail-label {
    opacity: 1;
}

/* --------------------------------------------------------------------------
   MAIN CONTENT AREA
   -------------------------------------------------------------------------- */
.main-content {
    margin-left: var(--rail-width);
    margin-top: var(--topbar-height);
    margin-bottom: var(--quickbar-height);
    padding: var(--space-xl);
    min-height: calc(100vh - var(--topbar-height) - var(--quickbar-height));
}

/* --------------------------------------------------------------------------
   QUICK ACCESS STRIP
   -------------------------------------------------------------------------- */
.quick-access {
    position: fixed;
    bottom: 0;
    left: var(--rail-width);
    right: 0;
    height: var(--quickbar-height);
    background: rgba(15, 17, 21, 0.9);
    backdrop-filter: blur(10px);
    border-top: 1px solid var(--chrome);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-lg);
    padding: 0 var(--space-xl);
    z-index: 100;
}

/* --------------------------------------------------------------------------
   CARDS - Frosted Glass
   -------------------------------------------------------------------------- */
.card {
    background: rgba(26, 29, 36, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid var(--chrome);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    position: relative;
    transition: var(--transition-fast);
}

.card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius-lg);
    padding: 1px;
    background: linear-gradient(135deg, rgba(5, 217, 232, 0.2), transparent, rgba(255, 42, 109, 0.2));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
}

.card:hover {
    border-color: rgba(5, 217, 232, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-lg);
    padding-bottom: var(--space-md);
    border-bottom: 1px solid var(--chrome);
}

.card-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--holo-white);
}

/* Terminal bar header */
.card-terminal-header {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-md);
}

.terminal-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.terminal-dot.red { background: var(--danger); }
.terminal-dot.yellow { background: var(--warning); }
.terminal-dot.green { background: var(--success); }

/* --------------------------------------------------------------------------
   METRIC CARDS - Hexagonal Corners
   -------------------------------------------------------------------------- */
.metric-card {
    background: rgba(26, 29, 36, 0.7);
    backdrop-filter: blur(10px);
    padding: var(--space-lg);
    position: relative;
    clip-path: polygon(
        12px 0, calc(100% - 12px) 0, 100% 12px,
        100% calc(100% - 12px), calc(100% - 12px) 100%,
        12px 100%, 0 calc(100% - 12px), 0 12px
    );
    border: none;
    transition: var(--transition-fast);
}

.metric-card::before {
    content: '';
    position: absolute;
    inset: 0;
    clip-path: polygon(
        12px 0, calc(100% - 12px) 0, 100% 12px,
        100% calc(100% - 12px), calc(100% - 12px) 100%,
        12px 100%, 0 calc(100% - 12px), 0 12px
    );
    background: linear-gradient(135deg, var(--neon-cyan), var(--neon-pink));
    z-index: -1;
    padding: 1px;
    animation: border-trace 3s linear infinite;
}

@keyframes border-trace {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

.metric-card::after {
    content: '';
    position: absolute;
    inset: 1px;
    clip-path: polygon(
        12px 0, calc(100% - 12px) 0, 100% 12px,
        100% calc(100% - 12px), calc(100% - 12px) 100%,
        12px 100%, 0 calc(100% - 12px), 0 12px
    );
    background: rgba(26, 29, 36, 0.95);
    z-index: -1;
}

.metric-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--smoke);
    margin-bottom: var(--space-sm);
}

.metric-value {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--holo-white);
    text-shadow: var(--glow-sm) var(--neon-cyan);
    line-height: 1;
}

.metric-card.success .metric-value {
    color: var(--success);
    text-shadow: var(--glow-sm) var(--success);
}

.metric-card.warning .metric-value {
    color: var(--warning);
    text-shadow: var(--glow-sm) var(--warning);
}

.metric-card.danger .metric-value {
    color: var(--danger);
    text-shadow: var(--glow-sm) var(--danger);
}

.metric-card.info .metric-value {
    color: var(--neon-cyan);
    text-shadow: var(--glow-sm) var(--neon-cyan);
}

/* --------------------------------------------------------------------------
   BUTTONS
   -------------------------------------------------------------------------- */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-md);
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    cursor: pointer;
    border: none;
    transition: var(--transition-fast);
    position: relative;
    overflow: hidden;
}

.btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left var(--transition-med);
}

.btn:hover::before {
    left: 100%;
}

.btn-primary {
    background: var(--neon-pink);
    color: white;
    box-shadow: var(--glow-sm) var(--neon-pink);
}

.btn-primary:hover {
    box-shadow: var(--glow-md) var(--neon-pink);
    transform: translateY(-1px);
}

.btn-secondary {
    background: transparent;
    color: var(--neon-cyan);
    border: 1px solid var(--neon-cyan);
}

.btn-secondary:hover {
    background: rgba(5, 217, 232, 0.1);
    box-shadow: var(--glow-sm) var(--neon-cyan);
}

.btn-success {
    background: var(--success);
    color: var(--void);
    box-shadow: var(--glow-sm) var(--success);
}

.btn-danger {
    background: var(--danger);
    color: white;
    box-shadow: var(--glow-sm) var(--danger);
    animation: danger-pulse 2s ease-in-out infinite;
}

@keyframes danger-pulse {
    0%, 100% { box-shadow: var(--glow-sm) var(--danger); }
    50% { box-shadow: var(--glow-md) var(--danger); }
}

.btn-sm {
    padding: var(--space-xs) var(--space-md);
    font-size: 0.75rem;
}

/* --------------------------------------------------------------------------
   BADGES / STATUS
   -------------------------------------------------------------------------- */
.badge {
    display: inline-flex;
    align-items: center;
    padding: var(--space-xs) var(--space-md);
    border-radius: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-pending {
    background: rgba(255, 211, 0, 0.15);
    color: var(--warning);
    border: 1px solid rgba(255, 211, 0, 0.3);
    animation: pulse-glow-warning 2s ease-in-out infinite;
}

@keyframes pulse-glow-warning {
    0%, 100% { box-shadow: none; }
    50% { box-shadow: var(--glow-sm) var(--warning); }
}

.badge-completed {
    background: rgba(57, 255, 20, 0.15);
    color: var(--success);
    border: 1px solid rgba(57, 255, 20, 0.3);
}

.badge-failed {
    background: rgba(255, 10, 84, 0.15);
    color: var(--danger);
    border: 1px solid rgba(255, 10, 84, 0.3);
    animation: flicker 0.5s ease-in-out infinite;
}

@keyframes flicker {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* Holographic shine sweep */
.badge::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: shine-sweep 25s ease-in-out infinite;
}

@keyframes shine-sweep {
    0% { left: -100%; }
    50%, 100% { left: 200%; }
}

/* --------------------------------------------------------------------------
   FORM INPUTS
   -------------------------------------------------------------------------- */
.form-group {
    margin-bottom: var(--space-lg);
}

.form-label {
    display: block;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--smoke);
    margin-bottom: var(--space-sm);
}

.form-input,
.form-textarea,
.form-select {
    width: 100%;
    background: var(--obsidian);
    border: 1px solid var(--chrome);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    color: var(--holo-white);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.875rem;
    transition: var(--transition-fast);
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
    outline: none;
    border-color: var(--neon-cyan);
    box-shadow: var(--glow-sm) var(--neon-cyan), inset 0 0 20px rgba(5, 217, 232, 0.05);
}

.form-textarea {
    min-height: 120px;
    resize: vertical;
}

/* --------------------------------------------------------------------------
   CHAT COMPONENTS
   -------------------------------------------------------------------------- */
.chat-container {
    background: rgba(10, 10, 12, 0.8);
    border: 1px solid var(--chrome);
    border-radius: var(--radius-lg);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-lg);
}

.chat-message {
    display: flex;
    gap: var(--space-md);
    margin-bottom: var(--space-lg);
    max-width: 85%;
    animation: message-appear 0.3s ease-out;
}

@keyframes message-appear {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.chat-message.warden {
    margin-right: auto;
}

.chat-message.user {
    margin-left: auto;
    flex-direction: row-reverse;
}

.chat-avatar {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
}

.chat-message.warden .chat-avatar {
    background: linear-gradient(135deg, var(--neon-pink), var(--neon-purple));
    box-shadow: var(--glow-sm) var(--neon-pink);
}

.chat-message.user .chat-avatar {
    background: var(--steel);
    border: 1px solid var(--neon-cyan);
    box-shadow: var(--glow-sm) var(--neon-cyan);
}

.chat-bubble {
    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);
    font-size: 0.9375rem;
    line-height: 1.6;
}

.chat-message.warden .chat-bubble {
    background: rgba(26, 29, 36, 0.8);
    border: 1px solid var(--chrome);
    border-left: 3px solid var(--neon-pink);
    border-bottom-left-radius: var(--radius-sm);
}

.chat-message.user .chat-bubble {
    background: rgba(5, 217, 232, 0.1);
    border: 1px solid rgba(5, 217, 232, 0.3);
    border-bottom-right-radius: var(--radius-sm);
}

.chat-time {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6875rem;
    color: var(--ash);
    margin-top: var(--space-xs);
}

.chat-type {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--neon-pink);
    margin-bottom: var(--space-xs);
}

.chat-input-container {
    padding: var(--space-md) var(--space-lg);
    background: rgba(15, 17, 21, 0.9);
    border-top: 1px solid var(--chrome);
}

.chat-input-container form {
    display: flex;
    gap: var(--space-md);
    align-items: center;
}

.chat-input {
    flex: 1;
    background: var(--obsidian);
    border: 1px solid var(--chrome);
    border-radius: 24px;
    padding: var(--space-md) var(--space-lg);
    color: var(--holo-white);
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9375rem;
    transition: var(--transition-fast);
}

.chat-input:focus {
    outline: none;
    border-color: var(--neon-cyan);
    box-shadow: var(--glow-sm) var(--neon-cyan);
}

.chat-send-btn {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--neon-pink);
    border: none;
    color: white;
    font-size: 1.25rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: var(--transition-fast);
    box-shadow: var(--glow-sm) var(--neon-pink);
}

.chat-send-btn:hover {
    transform: scale(1.05);
    box-shadow: var(--glow-md) var(--neon-pink);
}

.chat-send-btn:disabled {
    background: var(--chrome);
    box-shadow: none;
    cursor: not-allowed;
}

.chat-send-btn.loading {
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* --------------------------------------------------------------------------
   LISTS
   -------------------------------------------------------------------------- */
.list-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-md) 0;
    border-bottom: 1px solid var(--chrome);
    transition: var(--transition-fast);
}

.list-item:last-child {
    border-bottom: none;
}

.list-item:hover {
    background: rgba(5, 217, 232, 0.03);
    padding-left: var(--space-sm);
    padding-right: var(--space-sm);
    margin: 0 calc(-1 * var(--space-sm));
}

.list-item-title {
    font-weight: 500;
    margin-bottom: var(--space-xs);
}

.list-item-meta {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--smoke);
}

.list-item-actions {
    display: flex;
    gap: var(--space-sm);
}

/* --------------------------------------------------------------------------
   PATTERNS
   -------------------------------------------------------------------------- */
.pattern-item {
    background: rgba(26, 29, 36, 0.6);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-bottom: var(--space-md);
    border-left: 3px solid var(--danger);
    transition: var(--transition-fast);
}

.pattern-item:hover {
    background: rgba(26, 29, 36, 0.8);
}

.pattern-item.medium {
    border-left-color: var(--warning);
}

.pattern-item.low {
    border-left-color: var(--success);
}

.pattern-type {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--space-xs);
    color: var(--holo-white);
}

.pattern-desc {
    font-size: 0.875rem;
    color: var(--smoke);
}

/* --------------------------------------------------------------------------
   TABS
   -------------------------------------------------------------------------- */
.tabs {
    display: flex;
    gap: var(--space-xs);
    background: var(--obsidian);
    padding: var(--space-xs);
    border-radius: var(--radius-md);
    border: 1px solid var(--chrome);
    margin-bottom: var(--space-lg);
}

.tab {
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-sm);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    cursor: pointer;
    color: var(--smoke);
    background: none;
    border: none;
    transition: var(--transition-fast);
}

.tab:hover {
    color: var(--holo-white);
    background: rgba(5, 217, 232, 0.1);
}

.tab.active {
    background: var(--steel);
    color: var(--neon-cyan);
    box-shadow: 0 0 10px rgba(5, 217, 232, 0.2);
}

/* --------------------------------------------------------------------------
   GRIDS
   -------------------------------------------------------------------------- */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-lg);
    margin-bottom: var(--space-xl);
}

.grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-lg);
}

.grid-3 {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--space-lg);
}

/* --------------------------------------------------------------------------
   PAGE HEADER
   -------------------------------------------------------------------------- */
.page-header {
    margin-bottom: var(--space-xl);
}

.page-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: var(--space-sm);
    background: linear-gradient(90deg, var(--holo-white), var(--neon-cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.page-subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9375rem;
    color: var(--smoke);
}

/* --------------------------------------------------------------------------
   SECTIONS
   -------------------------------------------------------------------------- */
.section {
    display: none;
}

.section.active {
    display: block;
    animation: fade-in 0.3s ease-out;
}

@keyframes fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* --------------------------------------------------------------------------
   AUTH OVERLAY
   -------------------------------------------------------------------------- */
.auth-overlay {
    position: fixed;
    inset: 0;
    background: var(--void);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.auth-card {
    background: rgba(26, 29, 36, 0.8);
    backdrop-filter: blur(20px);
    border: 1px solid var(--chrome);
    border-radius: var(--radius-lg);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 400px;
    text-align: center;
}

.auth-logo {
    width: 80px;
    height: 80px;
    margin: 0 auto var(--space-lg);
    background: linear-gradient(135deg, var(--neon-pink), var(--neon-purple));
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: var(--glow-lg) var(--neon-pink);
    animation: logo-pulse 3s ease-in-out infinite;
}

@keyframes logo-pulse {
    0%, 100% { box-shadow: var(--glow-md) var(--neon-pink); }
    50% { box-shadow: var(--glow-xl) var(--neon-pink); }
}

.auth-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.5rem;
    margin-bottom: var(--space-sm);
}

.auth-subtitle {
    color: var(--smoke);
    margin-bottom: var(--space-xl);
}

/* --------------------------------------------------------------------------
   TOAST NOTIFICATIONS
   -------------------------------------------------------------------------- */
.toast {
    position: fixed;
    bottom: calc(var(--quickbar-height) + var(--space-lg));
    right: var(--space-lg);
    background: rgba(26, 29, 36, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid var(--chrome);
    border-radius: var(--radius-md);
    padding: var(--space-md) var(--space-lg);
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.875rem;
    display: none;
    z-index: 1000;
    animation: toast-in 0.3s ease-out;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
}

@keyframes toast-in {
    from {
        opacity: 0;
        transform: translateX(100px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.toast.show {
    display: block;
}

.toast.success {
    border-left: 3px solid var(--success);
}

.toast.error {
    border-left: 3px solid var(--danger);
}

/* --------------------------------------------------------------------------
   EMPTY STATES
   -------------------------------------------------------------------------- */
.empty-state {
    text-align: center;
    padding: var(--space-2xl);
    color: var(--ash);
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: var(--space-md);
    opacity: 0.5;
}

/* --------------------------------------------------------------------------
   CALENDAR
   -------------------------------------------------------------------------- */
.calendar-event {
    display: flex;
    gap: var(--space-md);
    padding: var(--space-md) 0;
    border-bottom: 1px solid var(--chrome);
}

.calendar-event:last-child {
    border-bottom: none;
}

.event-time {
    width: 70px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--neon-cyan);
}

.event-title {
    font-weight: 500;
}

.event-location {
    font-size: 0.8125rem;
    color: var(--ash);
}

/* --------------------------------------------------------------------------
   RESPONSIVE
   -------------------------------------------------------------------------- */
@media (max-width: 1100px) {
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 900px) {
    .grid-2,
    .grid-3 {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    :root {
        --rail-width: 0;
        --topbar-height: 60px;
    }

    .command-rail {
        left: -200px;
        width: 200px;
        transition: left var(--transition-med);
    }

    .command-rail.open {
        left: 0;
    }

    .command-rail .rail-label {
        opacity: 1;
    }

    .top-bar {
        left: 0;
    }

    .main-content {
        margin-left: 0;
        padding: var(--space-md);
    }

    .quick-access {
        left: 0;
    }

    .metrics-grid {
        grid-template-columns: 1fr 1fr;
    }

    .page-title {
        font-size: 1.25rem;
    }

    .mobile-header {
        display: flex !important;
    }

    .sidebar-overlay.active {
        display: block;
    }
}

/* Mobile header */
.mobile-header {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: rgba(15, 17, 21, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--chrome);
    padding: 0 var(--space-md);
    align-items: center;
    justify-content: space-between;
    z-index: 150;
}

.hamburger {
    background: none;
    border: none;
    color: var(--holo-white);
    font-size: 1.5rem;
    cursor: pointer;
    padding: var(--space-sm);
}

.sidebar-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 199;
}

/* --------------------------------------------------------------------------
   REDUCED MOTION
   -------------------------------------------------------------------------- */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }

    .bg-rain,
    .bg-fog,
    .bg-scanlines {
        display: none;
    }
}

/* --------------------------------------------------------------------------
   UTILITY CLASSES
   -------------------------------------------------------------------------- */
.text-pink { color: var(--neon-pink); }
.text-cyan { color: var(--neon-cyan); }
.text-success { color: var(--success); }
.text-warning { color: var(--warning); }
.text-danger { color: var(--danger); }
.text-muted { color: var(--smoke); }

.glow-pink { text-shadow: var(--glow-sm) var(--neon-pink); }
.glow-cyan { text-shadow: var(--glow-sm) var(--neon-cyan); }

.mb-0 { margin-bottom: 0; }
.mb-sm { margin-bottom: var(--space-sm); }
.mb-md { margin-bottom: var(--space-md); }
.mb-lg { margin-bottom: var(--space-lg); }
.mb-xl { margin-bottom: var(--space-xl); }

.mt-md { margin-top: var(--space-md); }
.mt-lg { margin-top: var(--space-lg); }

.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
.gap-lg { gap: var(--space-lg); }
    </style>
</head>
<body>
    <!-- Background Layers -->
    <div class="bg-base"></div>
    <div class="bg-grid"></div>
    <div class="bg-rain" id="rain-container"></div>
    <div class="bg-fog"></div>
    <div class="bg-scanlines"></div>

    <!-- Auth Overlay -->
    <div id="auth-overlay" class="auth-overlay">
        <div class="auth-card">
            <div class="auth-logo">&#x1F512;</div>
            <h1 class="auth-title">The Warden</h1>
            <p class="auth-subtitle">Enter your API key to continue</p>
            <div class="form-group">
                <input type="password" id="apiKeyInput" class="form-input" placeholder="API Key" />
            </div>
            <button class="btn btn-primary" style="width: 100%;" onclick="authenticate()">Connect</button>
        </div>
    </div>

    <!-- Mobile Header -->
    <header class="mobile-header" id="mobile-header" style="display: none;">
        <button class="hamburger" onclick="toggleSidebar()">&#9776;</button>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">&#x1F512;</span>
            <span style="font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 0.875rem; letter-spacing: 0.1em;">THE WARDEN</span>
        </div>
        <div style="width: 40px;"></div>
    </header>

    <!-- Sidebar Overlay (Mobile) -->
    <div class="sidebar-overlay" id="sidebar-overlay" onclick="closeSidebar()"></div>

    <!-- Main App Container -->
    <div id="app" style="display: none;">

        <!-- Command Rail (Navigation) -->
        <nav class="command-rail" id="sidebar">
            <div class="rail-logo"><i class="ph-bold ph-shield-chevron"></i></div>
            <div class="rail-nav">
                <a class="rail-item active" onclick="showSection('dashboard')">
                    <span class="rail-icon"><i class="ph-bold ph-monitor"></i></span>
                    <span class="rail-label">Command</span>
                </a>
                <a class="rail-item" onclick="showSection('chat')">
                    <span class="rail-icon"><i class="ph-bold ph-chat-centered-text"></i></span>
                    <span class="rail-label">Comms</span>
                </a>
                <a class="rail-item" onclick="showSection('commitments')">
                    <span class="rail-icon"><i class="ph-bold ph-crosshair"></i></span>
                    <span class="rail-label">Missions</span>
                </a>
                <a class="rail-item" onclick="showSection('goals')">
                    <span class="rail-icon"><i class="ph-bold ph-flag-pennant"></i></span>
                    <span class="rail-label">Objectives</span>
                </a>
                <a class="rail-item" onclick="showSection('calendar')">
                    <span class="rail-icon"><i class="ph-bold ph-calendar-blank"></i></span>
                    <span class="rail-label">Temporal</span>
                </a>
                <a class="rail-item" onclick="showSection('settings')">
                    <span class="rail-icon"><i class="ph-bold ph-gear-six"></i></span>
                    <span class="rail-label">Systems</span>
                </a>
                <a class="rail-item" onclick="showSection('errors')">
                    <span class="rail-icon"><i class="ph-bold ph-warning"></i></span>
                    <span class="rail-label">Debug</span>
                    <span id="error-count-badge" class="badge badge-pending" style="margin-left: auto; display: none;">0</span>
                </a>
            </div>
        </nav>

        <!-- Top Bar -->
        <header class="top-bar">
            <div class="top-bar-left">
                <span class="top-bar-logo">THE WARDEN</span>
                <div class="system-status">
                    <span class="status-dot"></span>
                    <span>SYSTEM ONLINE</span>
                </div>
            </div>
            <div class="top-bar-right">
                <span class="top-bar-time" id="current-time"></span>
            </div>
        </header>

        <!-- Main Content Area -->
        <main class="main-content">

            <!-- ============================================================
                 COMMAND (Dashboard) Section
                 ============================================================ -->
            <section id="section-dashboard" class="section active">
                <div class="page-header">
                    <h1 class="page-title">Command Center</h1>
                    <p class="page-subtitle">Your accountability at a glance</p>
                </div>

                <!-- Metrics Grid -->
                <div class="metrics-grid">
                    <div class="metric-card success">
                        <div class="metric-label">Completion Rate</div>
                        <div class="metric-value" id="metric-completion">--%</div>
                    </div>
                    <div class="metric-card warning">
                        <div class="metric-label">Pending Missions</div>
                        <div class="metric-value" id="metric-pending">--</div>
                    </div>
                    <div class="metric-card info">
                        <div class="metric-label">Response Streak</div>
                        <div class="metric-value" id="metric-response-streak">--</div>
                        <div class="metric-label" style="margin-top:4px;font-size:0.6875rem;" id="streak-response-best"></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Completion Streak</div>
                        <div class="metric-value" id="metric-completion-streak">--</div>
                        <div class="metric-label" style="margin-top:4px;font-size:0.6875rem;" id="streak-completion-best"></div>
                    </div>
                </div>

                <!-- Recent Activity & Patterns -->
                <div class="grid-3">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Recent Ops</h3>
                            <button class="btn btn-sm btn-secondary" onclick="triggerCheckin()"><i class="ph-bold ph-bell-ringing"></i> Trigger Check-in</button>
                        </div>
                        <div id="recent-activity"><div class="empty-state">Loading...</div></div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Active Patterns</h3>
                        </div>
                        <div id="patterns-list"><div class="empty-state">Loading...</div></div>
                    </div>
                </div>
            </section>

            <!-- ============================================================
                 COMMS (Chat) Section
                 ============================================================ -->
            <section id="section-chat" class="section">
                <div class="page-header">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                        <div>
                            <h1 class="page-title">Communications</h1>
                            <p class="page-subtitle">Your dialogue with The Warden</p>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <label style="font-size: 0.75rem; color: var(--smoke); font-family: 'Share Tech Mono', monospace;">LLM CONTEXT:</label>
                                <input type="number" id="chat-history-count" class="form-input" style="width: 60px; padding: 4px 8px;" value="15" min="0" max="100" onchange="updateChatHistoryCount(this.value)" />
                                <span style="font-size: 0.6875rem; color: var(--ash);">msgs</span>
                            </div>
                            <button class="btn btn-secondary btn-sm" onclick="loadChatHistory()">Refresh</button>
                        </div>
                    </div>
                </div>

                <div class="chat-container" style="height: 500px;">
                    <div class="chat-messages" id="chat-messages">
                        <div class="empty-state">Loading...</div>
                    </div>
                    <div class="chat-input-container">
                        <form id="chat-form" onsubmit="sendChatMessage(event)">
                            <input type="text" id="chat-input" class="chat-input" placeholder="Message The Warden..." autocomplete="off" />
                            <button type="submit" id="chat-send-btn" class="chat-send-btn" title="Send message">
                                <span id="chat-send-icon">&#x27A4;</span>
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Memory Panel -->
                <div class="card mt-lg">
                    <div class="card-header" style="cursor: pointer;" onclick="toggleMemoryPanel()">
                        <h3 class="card-title"><i class="ph-bold ph-brain"></i> Warden's Memory</h3>
                        <span id="memory-toggle-icon" style="font-size: 1.125rem;">&#x25BC;</span>
                    </div>
                    <div id="memory-panel" style="display: none;">
                        <p style="color: var(--smoke); font-size: 0.8125rem; margin-bottom: 12px;">
                            The Warden's learned observations about you. Updates automatically after conversations.
                        </p>
                        <div class="form-group">
                            <textarea id="llm-memory" class="form-textarea" style="min-height: 200px;"></textarea>
                        </div>
                        <div style="display: flex; gap: 8px; margin-bottom: 24px;">
                            <button class="btn btn-primary" onclick="saveMemory()">Save Memory</button>
                            <button class="btn btn-secondary" onclick="clearMemory()">Clear All</button>
                        </div>

                        <!-- User Profile Sub-section -->
                        <div style="border-top: 1px solid var(--chrome); padding-top: 16px;">
                            <h4 style="color: var(--smoke); font-size: 0.875rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                                <i class="ph-bold ph-user-circle"></i> User Information
                            </h4>
                            <p style="color: var(--ash); font-size: 0.75rem; margin-bottom: 16px;">
                                Personal facts the Warden knows about you. Updates silently during conversations.
                            </p>

                            <!-- Personal Section -->
                            <div class="profile-section" style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <label style="font-size: 0.8125rem; color: var(--smoke); font-weight: 600;">Personal</label>
                                    <button class="btn btn-secondary" style="font-size: 0.6875rem; padding: 4px 8px;" onclick="addProfileItem('personal')">+ Add</button>
                                </div>
                                <div id="profile-personal" class="profile-items" style="display: flex; flex-direction: column; gap: 4px;"></div>
                            </div>

                            <!-- Work Section -->
                            <div class="profile-section" style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <label style="font-size: 0.8125rem; color: var(--smoke); font-weight: 600;">Work</label>
                                    <button class="btn btn-secondary" style="font-size: 0.6875rem; padding: 4px 8px;" onclick="addProfileItem('work')">+ Add</button>
                                </div>
                                <div id="profile-work" class="profile-items" style="display: flex; flex-direction: column; gap: 4px;"></div>
                            </div>

                            <!-- Health Section -->
                            <div class="profile-section" style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <label style="font-size: 0.8125rem; color: var(--smoke); font-weight: 600;">Health</label>
                                    <button class="btn btn-secondary" style="font-size: 0.6875rem; padding: 4px 8px;" onclick="addProfileItem('health')">+ Add</button>
                                </div>
                                <div id="profile-health" class="profile-items" style="display: flex; flex-direction: column; gap: 4px;"></div>
                            </div>

                            <!-- Other Section -->
                            <div class="profile-section" style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <label style="font-size: 0.8125rem; color: var(--smoke); font-weight: 600;">Other</label>
                                    <button class="btn btn-secondary" style="font-size: 0.6875rem; padding: 4px 8px;" onclick="addProfileItem('other')">+ Add</button>
                                </div>
                                <div id="profile-other" class="profile-items" style="display: flex; flex-direction: column; gap: 4px;"></div>
                            </div>

                            <div style="display: flex; gap: 8px; margin-top: 16px;">
                                <button class="btn btn-primary" onclick="saveUserProfile()">Save Profile</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Agent Intelligence Panel -->
                <div class="card mt-md">
                    <div class="card-header" style="cursor: pointer;" onclick="toggleAgentPanel()">
                        <h3 class="card-title"><i class="ph-bold ph-robot"></i> Agent Intelligence</h3>
                        <span id="agent-toggle-icon" style="font-size: 1.125rem;">&#x25BC;</span>
                    </div>
                    <div id="agent-panel" style="display: none;">
                        <!-- Accountability Intensity -->
                        <div style="padding: 16px; border-bottom: 1px solid var(--chrome);">
                            <label class="form-label">Accountability Intensity</label>
                            <div style="display: flex; align-items: center; gap: 16px;">
                                <input type="range" id="intensity-slider" min="1" max="5" value="3" style="flex: 1;" onchange="updateIntensity(this.value)">
                                <span id="intensity-label" style="min-width: 120px; color: var(--smoke); font-family: 'Share Tech Mono', monospace;">Balanced (3)</span>
                            </div>
                            <p style="font-size: 0.75rem; color: var(--ash); margin-top: 8px;">
                                1 = Gentle & supportive &bull; 3 = Balanced &bull; 5 = Intense & demanding
                            </p>
                        </div>

                        <!-- Thinking Level -->
                        <div style="padding: 16px; border-bottom: 1px solid var(--chrome);">
                            <label class="form-label">Thinking Level (Reasoning Depth)</label>
                            <div style="display: flex; align-items: center; gap: 12px; margin-top: 8px;">
                                <select id="thinking-level" class="form-input" style="width: auto;" onchange="updateThinkingLevel(this.value)">
                                    <option value="off">Off (Fastest)</option>
                                    <option value="minimal">Minimal</option>
                                    <option value="low">Low</option>
                                    <option value="medium" selected>Medium (Recommended)</option>
                                    <option value="high">High (Deepest)</option>
                                </select>
                                <span id="thinking-cost" style="font-size: 0.75rem; color: var(--ash);">&#x1F4B0; Moderate cost</span>
                            </div>
                            <p style="font-size: 0.75rem; color: var(--ash); margin-top: 8px;">
                                Higher = better judgment but slower & more expensive.
                            </p>
                        </div>

                        <!-- Mood Trend -->
                        <div style="padding: 16px; border-bottom: 1px solid var(--chrome);">
                            <label class="form-label">Mood Trend (Last 7 Days)</label>
                            <div id="mood-trend" style="display: flex; gap: 16px; margin-top: 8px;">
                                <div style="text-align: center;">
                                    <div style="font-size: 1.5rem;" id="avg-mood-icon">&#x1F610;</div>
                                    <div style="font-size: 0.75rem; color: var(--ash);">Avg Mood</div>
                                    <div id="avg-mood-value" style="font-weight: 600;">--</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-size: 1.5rem;">&#x26A1;</div>
                                    <div style="font-size: 0.75rem; color: var(--ash);">Avg Energy</div>
                                    <div id="avg-energy-value" style="font-weight: 600;">--</div>
                                </div>
                            </div>
                        </div>

                        <!-- Scheduled Follow-ups -->
                        <div style="padding: 16px;">
                            <label class="form-label">Scheduled Follow-ups</label>
                            <div id="followups-list" style="margin-top: 8px;">
                                <div class="empty-state" style="padding: 16px; font-size: 0.8125rem;">No scheduled follow-ups</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================================
                 MISSIONS (Commitments) Section
                 ============================================================ -->
            <section id="section-commitments" class="section">
                <div class="page-header">
                    <h1 class="page-title">Active Missions</h1>
                    <p class="page-subtitle">Track what you've promised to deliver</p>
                </div>

                <!-- Add Commitment Form -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">New Mission</h3>
                    </div>
                    <form onsubmit="createCommitment(event)">
                        <div class="grid-2">
                            <div class="form-group">
                                <label class="form-label">Mission Objective</label>
                                <input type="text" id="commit-title" class="form-input" placeholder="What are you committing to?" required />
                            </div>
                            <div class="form-group">
                                <label class="form-label">Deadline</label>
                                <div style="display: flex; gap: 8px;">
                                    <input type="date" id="commit-due" class="form-input" style="flex: 1;" />
                                    <input type="time" id="commit-time" class="form-input" style="width: 120px;" value="12:00" />
                                </div>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Mission</button>
                    </form>
                </div>

                <!-- Tabs -->
                <div class="tabs">
                    <button class="tab active" onclick="filterCommitments('pending')">[PENDING]</button>
                    <button class="tab" onclick="filterCommitments('completed')">[COMPLETE]</button>
                    <button class="tab" onclick="filterCommitments('failed')">[FAILED]</button>
                </div>

                <!-- Commitments List -->
                <div class="card">
                    <div id="commitments-list">
                        <div class="empty-state">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- ============================================================
                 OBJECTIVES (Goals) Section
                 ============================================================ -->
            <section id="section-goals" class="section">
                <div class="page-header">
                    <h1 class="page-title">Strategic Objectives</h1>
                    <p class="page-subtitle">What are you working toward?</p>
                </div>

                <!-- Add Goal Form -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">New Objective</h3>
                    </div>
                    <form onsubmit="createGoal(event)">
                        <div class="form-group">
                            <label class="form-label">Objective Title</label>
                            <input type="text" id="goal-title" class="form-input" required />
                        </div>
                        <div class="grid-2">
                            <div class="form-group">
                                <label class="form-label">Description</label>
                                <input type="text" id="goal-desc" class="form-input" />
                            </div>
                            <div class="form-group">
                                <label class="form-label">Target Date</label>
                                <input type="date" id="goal-date" class="form-input" />
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Objective</button>
                    </form>
                </div>

                <!-- Goals List -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Active Objectives</h3>
                    </div>
                    <div id="goals-list">
                        <div class="empty-state">Loading...</div>
                    </div>
                </div>
            </section>

            <!-- ============================================================
                 TEMPORAL (Calendar) Section
                 ============================================================ -->
            <section id="section-calendar" class="section">
                <div class="page-header">
                    <h1 class="page-title">Temporal View</h1>
                    <p class="page-subtitle">Upcoming events, missions, and deadlines</p>
                </div>

                <!-- Calendar Status -->
                <div class="card mb-md">
                    <div class="card-header">
                        <h3 class="card-title">Google Calendar Status</h3>
                        <span id="calendar-sync-status" class="badge badge-pending">Not synced</span>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
                        <button class="btn btn-primary" onclick="syncCalendar()">Sync Calendar</button>
                        <button class="btn btn-secondary" onclick="addManualEvent()">+ Manual Event</button>
                        <span id="last-sync-info" style="color: var(--ash); font-size: 0.8125rem; font-family: 'Share Tech Mono', monospace;"></span>
                    </div>
                </div>

                <!-- Upcoming Commitments -->
                <div class="card mb-md">
                    <div class="card-header">
                        <h3 class="card-title"><i class="ph-bold ph-list-checks"></i> Upcoming Missions</h3>
                        <span id="commitment-count" class="badge badge-pending">0</span>
                    </div>
                    <div id="calendar-commitments">
                        <div class="empty-state">No pending missions with deadlines</div>
                    </div>
                </div>

                <!-- Calendar Events -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title"><i class="ph-bold ph-calendar-blank"></i> Calendar Events (14 days)</h3>
                        <span id="event-count" class="badge badge-pending">0</span>
                    </div>
                    <div id="calendar-events">
                        <div class="empty-state">
                            <div class="empty-state-icon"><i class="ph-bold ph-calendar-blank" style="font-size: 2rem;"></i></div>
                            <p>No upcoming events. Connect Google Calendar in Systems.</p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ============================================================
                 SYSTEMS (Settings) Section
                 ============================================================ -->
            <section id="section-settings" class="section">
                <div class="page-header">
                    <h1 class="page-title">Systems Config</h1>
                    <p class="page-subtitle">Configure The Warden's behavior</p>
                </div>

                <div class="grid-2">
                    <!-- LLM Model Selection -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">LLM Model<span id="model-count" style="font-size: 0.75rem; color: var(--smoke); margin-left: 8px;"></span></h3>
                        </div>
                        <select id="model-selector" class="form-input" onchange="selectModel(this.value)">
                            <option value="">Loading models...</option>
                        </select>
                        <div id="model-info" class="mt-md" style="display: none; padding: 12px; background: var(--obsidian); border-radius: 8px; font-size: 0.75rem;">
                            <div style="color: var(--ash); margin-bottom: 4px;">Model ID</div>
                            <div id="model-id-display" style="color: var(--holo-white); font-family: 'Share Tech Mono', monospace;"></div>
                        </div>
                    </div>

                    <!-- Quick Actions -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Quick Actions</h3>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            <button class="btn btn-secondary" onclick="triggerCheckin()"><i class="ph-bold ph-bell-ringing"></i> Trigger Check-in</button>
                            <button class="btn btn-secondary" onclick="triggerWeeklyReview()"><i class="ph-bold ph-chart-line-up"></i> Trigger Weekly Review</button>
                        </div>
                    </div>
                </div>

                <!-- Check-in Schedules -->
                <div class="card mt-lg">
                    <div class="card-header">
                        <h3 class="card-title"><i class="ph-bold ph-clock"></i> Check-in Schedules</h3>
                        <button class="btn btn-sm btn-primary" onclick="showAddScheduleForm()">+ Add Schedule</button>
                    </div>
                    <p style="color: var(--smoke); font-size: 0.8125rem; margin-bottom: 16px;">
                        Configure when The Warden checks in with you.
                    </p>
                    <div id="schedules-list"><div class="empty-state">Loading schedules...</div></div>
                    <div id="add-schedule-form" style="display: none; margin-top: 16px; padding: 16px; background: var(--obsidian); border-radius: 8px;">
                        <h4 id="schedule-form-title" style="margin-bottom: 12px; font-family: 'Orbitron', sans-serif; font-size: 0.875rem;">Add New Schedule</h4>
                        <div class="grid-2" style="margin-bottom: 12px;">
                            <div class="form-group mb-0">
                                <label class="form-label">Name</label>
                                <input type="text" id="sched-name" class="form-input" placeholder="e.g., Morning Check-in" />
                            </div>
                            <div class="form-group mb-0">
                                <label class="form-label">Type</label>
                                <select id="sched-type" class="form-input">
                                    <option value="daily_checkin">Morning Check-in</option>
                                    <option value="custom_reminder">Custom Reminder</option>
                                    <option value="weekly_review">Weekly Review</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid-2" style="margin-bottom: 12px;">
                            <div class="form-group mb-0">
                                <label class="form-label">Time</label>
                                <input type="time" id="sched-time" class="form-input" value="09:00" />
                            </div>
                            <div class="form-group mb-0">
                                <label class="form-label">Days (blank = every day)</label>
                                <input type="text" id="sched-days" class="form-input" placeholder="mon,tue,wed,thu,fri" />
                            </div>
                        </div>
                        <div class="form-group" style="margin-bottom: 12px;">
                            <label class="form-label">Custom Prompt (optional)</label>
                            <textarea id="sched-prompt" class="form-textarea" style="min-height: 80px;" placeholder="Custom instructions for this check-in..."></textarea>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button id="schedule-save-btn" class="btn btn-primary" onclick="saveSchedule()">Save Schedule</button>
                            <button class="btn btn-secondary" onclick="hideAddScheduleForm()">Cancel</button>
                        </div>
                    </div>
                </div>

                <!-- Quiet Hours -->
                <div class="card mt-lg">
                    <div class="card-header">
                        <h3 class="card-title"><i class="ph-bold ph-moon-stars"></i> Quiet Hours</h3>
                    </div>
                    <p style="color: var(--smoke); font-size: 0.8125rem; margin-bottom: 16px;">
                        During quiet hours, The Warden won't send scheduled messages.
                    </p>
                    <div class="form-group">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" id="quiet-hours-enabled" onchange="updateQuietHours()" />
                            <span>Enable Quiet Hours</span>
                            <span id="quiet-status" class="badge badge-pending" style="margin-left: 8px;"></span>
                        </label>
                    </div>
                    <div class="grid-2 mt-md">
                        <div class="form-group mb-0">
                            <label class="form-label">Start Time</label>
                            <input type="time" id="quiet-start" class="form-input" value="19:30" onchange="updateQuietHours()" />
                        </div>
                        <div class="form-group mb-0">
                            <label class="form-label">End Time</label>
                            <input type="time" id="quiet-end" class="form-input" value="04:00" onchange="updateQuietHours()" />
                        </div>
                    </div>
                </div>

                <!-- Check-in Prompts -->
                <div class="card mt-lg">
                    <div class="card-header">
                        <h3 class="card-title"><i class="ph-bold ph-text-aa"></i> Check-in Prompts</h3>
                    </div>
                    <p style="color: var(--smoke); font-size: 0.8125rem; margin-bottom: 16px;">
                        Customize prompts for different check-in types.
                    </p>
                    <div id="prompts-list"><div class="empty-state">Loading prompts...</div></div>
                    <div id="edit-prompt-form" style="display: none; margin-top: 16px; padding: 16px; background: var(--obsidian); border-radius: 8px;">
                        <h4 style="margin-bottom: 4px; font-family: 'Orbitron', sans-serif; font-size: 0.875rem;">Edit Prompt: <span id="edit-prompt-type"></span></h4>
                        <p style="color: var(--ash); font-size: 0.75rem; margin-bottom: 12px;">This prompt tells the LLM how to generate check-in messages.</p>
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

                <!-- System Prompt -->
                <div class="card mt-lg">
                    <div class="card-header">
                        <h3 class="card-title">System Prompt</h3>
                        <button class="btn btn-sm btn-secondary" onclick="resetPrompt()">Reset to Default</button>
                    </div>
                    <div class="form-group">
                        <textarea id="system-prompt" class="form-textarea" style="min-height: 300px;"></textarea>
                    </div>
                    <button class="btn btn-primary" onclick="savePrompt()">Save Prompt</button>
                </div>

                <!-- Google Calendar Integration -->
                <div class="card mt-lg">
                    <div class="card-header">
                        <h3 class="card-title">Google Calendar Integration</h3>
                        <span id="calendar-status" class="badge badge-pending">Not Connected</span>
                    </div>
                    <p style="color: var(--smoke); font-size: 0.8125rem; margin-bottom: 16px;">
                        Connect your Google Calendar for meeting-aware check-ins and OOO detection.
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
                            <p style="color: var(--warning); font-size: 0.8125rem; margin-bottom: 12px;">
                                After authorizing, paste the code from the redirect URL here:
                            </p>
                            <div class="form-group">
                                <label class="form-label">Authorization Code</label>
                                <input type="text" id="gcal-auth-code" class="form-input" placeholder="Paste the code from the URL" />
                            </div>
                            <button class="btn btn-success" onclick="submitAuthCode()">Submit Code</button>
                        </div>
                    </div>
                    <div style="margin-top: 16px; padding: 12px; background: var(--obsidian); border-radius: 8px; font-size: 0.75rem; color: var(--ash);">
                        <strong>Setup instructions:</strong><br>
                        1. Go to <a href="https://console.cloud.google.com" target="_blank" style="color: var(--neon-cyan);">Google Cloud Console</a><br>
                        2. Create a project and enable Google Calendar API<br>
                        3. Create OAuth 2.0 Client ID (Web application)<br>
                        4. Add redirect URI: <code style="background: var(--void); padding: 2px 6px; border-radius: 4px;">${window.location.origin}/api/calendar/callback</code>
                    </div>
                </div>

                <!-- Telegram Webhook -->
                <div class="card mt-lg">
                    <div class="card-header">
                        <h3 class="card-title">Telegram Webhook</h3>
                        <span id="webhook-status" class="badge badge-pending">Unknown</span>
                    </div>
                    <p style="color: var(--ash); font-size: 0.8125rem; margin-bottom: 16px;">
                        The webhook allows The Warden to receive your Telegram replies.
                    </p>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <button class="btn btn-primary" onclick="setupWebhook()">Setup Webhook</button>
                        <button class="btn btn-secondary" onclick="checkWebhookStatus()">Check Status</button>
                    </div>
                    <div id="webhook-info" style="margin-top: 12px; padding: 12px; background: var(--obsidian); border-radius: 8px; font-size: 0.75rem; display: none;">
                        <div id="webhook-details"></div>
                    </div>
                </div>
            </section>

            <!-- ============================================================
                 DEBUG (Errors) Section
                 ============================================================ -->
            <section id="section-errors" class="section">
                <div class="page-header">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                        <div>
                            <h1 class="page-title">Debug Console</h1>
                            <p class="page-subtitle">Track and resolve application errors</p>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-secondary btn-sm" onclick="loadErrors()">Refresh</button>
                            <button class="btn btn-success btn-sm" onclick="resolveAllErrors()">Resolve All</button>
                            <button class="btn btn-danger btn-sm" onclick="clearResolvedErrors()">Clear Resolved</button>
                        </div>
                    </div>
                </div>

                <!-- Error Metrics -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Errors</div>
                        <div class="metric-value" id="error-total">--</div>
                    </div>
                    <div class="metric-card warning">
                        <div class="metric-label">Unresolved</div>
                        <div class="metric-value" id="error-unresolved">--</div>
                    </div>
                    <div class="metric-card success">
                        <div class="metric-label">Resolved</div>
                        <div class="metric-value" id="error-resolved">--</div>
                    </div>
                    <div class="metric-card info">
                        <div class="metric-label">Last 24h</div>
                        <div class="metric-value" id="error-recent">--</div>
                    </div>
                </div>

                <!-- Errors List -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Recent Errors</h3>
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 0.8125rem; color: var(--smoke);">
                            <input type="checkbox" id="unresolved-only" onchange="loadErrors()"> Show unresolved only
                        </label>
                    </div>
                    <div id="errors-list"><div class="empty-state">Loading...</div></div>
                </div>

                <!-- Error Detail Modal -->
                <div id="error-detail-modal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center;">
                    <div style="background: var(--steel); border: 1px solid var(--chrome); border-radius: 12px; padding: 24px; max-width: 800px; width: 90%; max-height: 80vh; overflow-y: auto;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3 id="error-detail-title" style="font-size: 1.125rem; font-family: 'Orbitron', sans-serif;">Error Details</h3>
                            <button class="btn btn-secondary btn-sm" onclick="closeErrorDetail()">&#x2715; Close</button>
                        </div>
                        <div id="error-detail-content"></div>
                    </div>
                </div>
            </section>

        </main>

        <!-- Quick Access Strip -->
        <footer class="quick-access">
            <button class="btn btn-primary" onclick="triggerCheckin()"><i class="ph-bold ph-bell-ringing"></i> Trigger Check-in</button>
            <button class="btn btn-secondary" onclick="showSection('commitments'); document.getElementById('commit-title').focus();"><i class="ph-bold ph-plus"></i> New Mission</button>
            <button class="btn btn-secondary" onclick="showSection('chat'); document.getElementById('chat-input').focus();"><i class="ph-bold ph-chat-centered-text"></i> Quick Chat</button>
        </footer>

    </div>

    <!-- Toast Notifications -->
    <div id="toast" class="toast"></div>

    <!-- JAVASCRIPT PLACEHOLDER - Will be appended -->
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

// TEMPORARY: Bypass login and check database status directly
(async function() {
    // Show dashboard immediately without login
    document.getElementById('auth-overlay').style.display = 'none';
    document.getElementById('app').style.display = 'flex';
    document.getElementById('mobile-header').style.display = '';

    // Check database connection status
    try {
        const dbStatus = await fetch('/debug/db');
        const dbData = await dbStatus.json();
        if (dbData.connection === 'FAILED') {
            showToast('Database Error: ' + dbData.error_message, 'error');
            document.getElementById('recent-activity').innerHTML =
                '<div style="background: #2a1a1a; border: 1px solid #ef4444; border-radius: 8px; padding: 16px; color: #ef4444;">' +
                '<strong>Database Connection Failed</strong><br><br>' +
                '<strong>Error:</strong> ' + dbData.error_type + '<br>' +
                '<strong>Message:</strong> ' + dbData.error_message + '<br><br>' +
                '<strong>URL Prefix:</strong> ' + dbData.database_url_prefix + '<br>' +
                '<strong>Has Pooler:</strong> ' + dbData.database_url_contains_pooler + '<br>' +
                '<strong>Port:</strong> ' + dbData.database_url_port +
                '</div>';
        } else {
            showToast('Database connected!', 'success');
            loadDashboard();
        }
    } catch (e) {
        showToast('Failed to check database: ' + e.message, 'error');
    }
})();

// Original login code (disabled for now)
// if (API_KEY) { document.getElementById('apiKeyInput').value = API_KEY; authenticate(); }

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
    document.querySelectorAll('.rail-item').forEach(n => n.classList.remove('active'));
    document.getElementById('section-' + name).classList.add('active');
    event.target.closest('.rail-item').classList.add('active');
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
        ? checkins.map(c => `<div class="list-item"><div><div class="list-item-title">${c.response_received ? '<i class="ph-bold ph-check-circle" style="color: var(--success);"></i>' : '<i class="ph-bold ph-clock" style="color: var(--warning);"></i>'} ${c.check_in_type.replace('_', ' ')}</div><div class="list-item-meta">${new Date(c.sent_at).toLocaleString()}</div></div></div>`).join('')
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
    if (!messages || !messages.length) { container.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="ph-bold ph-chat-centered-text" style="font-size: 2rem;"></i></div><p>No messages yet. Say hi!</p></div>'; return; }
    container.innerHTML = messages.map(m => `<div class="chat-message ${m.role}"><div class="chat-avatar">${m.role === 'warden' ? '<i class="ph-bold ph-shield-chevron"></i>' : '<i class="ph-bold ph-user"></i>'}</div><div>${m.message_type ? `<div class="chat-type">${m.message_type.replace('_', ' ')}</div>` : ''}<div class="chat-bubble">${m.content}</div><div class="chat-time">${new Date(m.created_at).toLocaleString()}</div></div></div>`).join('');
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
    const userMsgHtml = `<div class="chat-message user"><div class="chat-avatar"><i class="ph-bold ph-user"></i></div><div><div class="chat-bubble">${escapeHtml(message)}</div><div class="chat-time">${new Date().toLocaleString()}</div></div></div>`;
    container.insertAdjacentHTML('beforeend', userMsgHtml);
    container.scrollTop = container.scrollHeight;

    // Clear input
    input.value = '';

    try {
        // Send message to API
        const response = await api('POST', '/settings/chat/send', { message });

        if (response && response.reply) {
            // Add Warden's reply to chat
            const wardenMsgHtml = `<div class="chat-message warden"><div class="chat-avatar"><i class="ph-bold ph-shield-chevron"></i></div><div><div class="chat-type">reply</div><div class="chat-bubble">${escapeHtml(response.reply)}</div><div class="chat-time">${new Date().toLocaleString()}</div></div></div>`;
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
        loadUserProfile();  // Load user profile when panel opens
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

// User Profile Functions
let userProfile = { personal: [], work: [], health: [], other: [] };

async function loadUserProfile() {
    const result = await api('GET', '/settings/user-profile');
    if (result && result.profile) {
        userProfile = result.profile;
        renderUserProfile();
    }
}

function renderUserProfile() {
    const sections = ['personal', 'work', 'health', 'other'];
    sections.forEach(section => {
        const container = document.getElementById(`profile-${section}`);
        if (!container) return;

        const items = userProfile[section] || [];
        if (items.length === 0) {
            container.innerHTML = '<span style="color: var(--ash); font-size: 0.75rem; font-style: italic;">No items yet</span>';
        } else {
            container.innerHTML = items.map((item, idx) => `
                <div style="display: flex; align-items: center; gap: 8px; background: var(--midnight); padding: 8px 12px; border-radius: 4px;">
                    <input type="text" value="${escapeHtml(item)}"
                           style="flex: 1; background: transparent; border: none; color: var(--smoke); font-size: 0.8125rem; outline: none;"
                           onchange="updateProfileItem('${section}', ${idx}, this.value)">
                    <button onclick="removeProfileItem('${section}', ${idx})"
                            style="background: none; border: none; color: var(--ash); cursor: pointer; padding: 2px; font-size: 1rem;"
                            title="Remove">&#x2715;</button>
                </div>
            `).join('');
        }
    });
}

function addProfileItem(section) {
    const item = prompt('Add new ' + section + ' info:');
    if (item && item.trim()) {
        if (!userProfile[section]) {
            userProfile[section] = [];
        }
        userProfile[section].push(item.trim());
        renderUserProfile();
    }
}

function updateProfileItem(section, idx, newValue) {
    if (userProfile[section] && userProfile[section][idx] !== undefined) {
        userProfile[section][idx] = newValue.trim();
    }
}

function removeProfileItem(section, idx) {
    if (userProfile[section]) {
        userProfile[section].splice(idx, 1);
        renderUserProfile();
    }
}

async function saveUserProfile() {
    const result = await api('PUT', '/settings/user-profile', userProfile);
    if (result) {
        showToast('Profile saved');
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
                            <div style="font-size: 12px; color: var(--text-muted);"><i class="ph-bold ph-calendar-blank"></i> ${dateStr} ${timeStr}</div>
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
        const dueDisplay = dueDate ? `<i class="ph-bold ph-calendar-blank"></i> ${dateStr} at ${timeStr}` : '';
        const deferredBadge = c.deferred_count > 0 ? `<span style="color: var(--warning);"><i class="ph-bold ph-arrow-counter-clockwise"></i> Deferred ${c.deferred_count}x</span>` : '';

        if (c.status === 'pending') {
            return `<div class="list-item">
                <div style="flex: 1;">
                    <div class="list-item-title">${c.title}</div>
                    <div class="list-item-meta">${dueDisplay} ${deferredBadge}</div>
                </div>
                <div class="list-item-actions" style="display: flex; gap: 8px; align-items: center;">
                    <button class="btn btn-sm btn-secondary" onclick="editCommitmentTime(${c.id}, '${c.title}', '${c.due_date || ''}')"><i class="ph-bold ph-calendar-blank"></i></button>
                    <button class="btn btn-sm btn-success" onclick="completeCommitment(${c.id})"><i class="ph-bold ph-check"></i></button>
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
    container.innerHTML = goals.map(g => `<div class="list-item"><div><div class="list-item-title">${g.title}</div><div class="list-item-meta">${g.description || ''} ${g.target_date ? '<i class="ph-bold ph-calendar-blank"></i> ' + new Date(g.target_date).toLocaleDateString() : ''}</div></div><div class="list-item-actions"><button class="btn btn-sm btn-danger" onclick="deleteGoal(${g.id})"><i class="ph-bold ph-trash"></i></button></div></div>`).join('');
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
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="ph-bold ph-calendar-blank" style="font-size: 2rem;"></i></div><p>No upcoming events. Connect Google Calendar in Settings to sync.</p></div>';
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
                <div class="list-item-meta"><i class="ph-bold ph-clock"></i> ${timeStr} • ${daysStr} • Type: ${s.check_in_type}</div>
                ${s.prompt_template ? '<div class="list-item-meta" style="font-style: italic; margin-top: 4px;">Custom prompt configured</div>' : ''}
            </div>
            <div class="list-item-actions">
                <button class="btn btn-sm btn-primary" onclick="editSchedule(${s.id}, '${s.name}', ${s.hour}, ${s.minute}, '${s.days_of_week || ''}', '${s.check_in_type}', \`${(s.prompt_template || '').replace(/`/g, '\\`')}\`)">Edit</button>
                <button class="btn btn-sm btn-secondary" onclick="toggleSchedule(${s.id}, ${!s.is_active})">${s.is_active ? 'Pause' : 'Enable'}</button>
                <button class="btn btn-sm btn-danger" onclick="deleteSchedule(${s.id})"><i class="ph-bold ph-trash"></i></button>
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
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="ph-bold ph-check-circle" style="font-size: 2rem; color: var(--success);"></i></div><p>No errors found. System is running smoothly!</p></div>';
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
                <div class="list-item-meta" style="margin-top: 4px; font-size: 11px;"><i class="ph-bold ph-calendar-blank"></i> ${date}</div>
            </div>
            <div class="list-item-actions" style="flex-shrink: 0;">
                <button class="btn btn-sm btn-secondary" onclick="viewErrorDetail(${e.id})">Details</button>
                ${!e.resolved ? `<button class="btn btn-sm btn-success" onclick="resolveError(${e.id})">Resolve</button>` : ''}
                <button class="btn btn-sm btn-danger" onclick="deleteError(${e.id})"><i class="ph-bold ph-trash"></i></button>
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

// Rain effect
function createRainDrop() {
    const rain = document.getElementById('rain-container');
    if (!rain) return;
    const drop = document.createElement('div');
    drop.className = 'rain-drop';
    drop.style.left = Math.random() * 100 + '%';
    drop.style.animationDuration = (Math.random() * 1 + 0.5) + 's';
    rain.appendChild(drop);
    setTimeout(() => drop.remove(), 2000);
}
setInterval(createRainDrop, 50);

// Update time display
function updateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    const dateStr = now.toLocaleDateString([], {weekday: 'short', month: 'short', day: 'numeric'});
    const el = document.getElementById('current-time');
    if (el) el.textContent = timeStr + ' • ' + dateStr;
}
setInterval(updateTime, 1000);
updateTime();
    </script>
</body>
</html>
"""
