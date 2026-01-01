# The Warden - Cyberpunk UI Overhaul Design

**Date:** 2026-01-01
**Aesthetic:** Blade Runner / Neo-Tokyo
**Approach:** Full immersion with animated effects
**Primary Use Case:** Quick glances throughout the day, dashboard-first

---

## Typography

| Purpose | Font | Notes |
|---------|------|-------|
| Headlines | Orbitron | Angular, futuristic, corporate-dystopia |
| Body/UI | Rajdhani | Clean but techy, great readability |
| Monospace/Data | Share Tech Mono | Metrics, code, timestamps |

---

## Color Palette

```css
:root {
    /* Void & Structure */
    --void:          #0a0a0c;
    --obsidian:      #0f1115;
    --steel:         #1a1d24;
    --chrome:        #2a2f3a;

    /* Neon Accents */
    --neon-pink:     #ff2a6d;
    --neon-cyan:     #05d9e8;
    --neon-blue:     #0ff0fc;
    --neon-purple:   #d300c5;

    /* Text */
    --holo-white:    #e8f0ff;
    --smoke:         #7a8599;
    --ash:           #4a5568;

    /* Status */
    --danger:        #ff0a54;
    --success:       #39ff14;
    --warning:       #ffd300;
}
```

---

## Background & Atmosphere

### Layered System (bottom to top):
1. **Base:** Deep void gradient with subtle noise texture, purple/blue undertones
2. **Grid:** Perspective grid fading into distance, thin cyan lines at 20% opacity
3. **Rain:** Animated falling particles, thin streaks at 15% opacity
4. **Fog/Glow:** Pink glow bottom-left, cyan glow top-right (distant neon signs)
5. **Scanlines:** Horizontal lines at 3% opacity (CRT terminal feel)

### Card Surfaces:
- Frosted glass effect (backdrop-blur)
- Thin glowing borders (1px with box-shadow glow)
- Holographic displays floating in the rain

---

## Navigation & Layout

### Top Bar (new):
- Thin ambient bar
- The Warden logo left, current time/date right
- Pulsing "system online" indicator
- Glitch effect on logo hover

### Command Rail (replaces sidebar):
- Slim, icon-based, collapsed by default
- Expands on hover with labels
- Icons have neon glow halos when active
- Sections:
  - COMMAND (Dashboard)
  - COMMS (Chat)
  - MISSIONS (Commitments)
  - OBJECTIVES (Goals)
  - TEMPORAL (Calendar)
  - SYSTEMS (Settings + Error Log)

### Quick Access Strip (new - bottom):
- Floating action bar, always visible
- "Trigger Check-in" / "New Commitment" / "Quick Chat"
- Keyboard shortcut hints

---

## Components

### Metric Cards:
- Hexagonal accent cuts on corners
- Large glowing numbers with text-shadow halos
- Animated counting on load
- Thin animated border trace
- Pulse animation on value update

### Data Cards:
- Frosted glass with 1px neon border
- Terminal bar header with colored dot indicators
- Subtle inner glow on edges
- Hover: border intensifies, slight lift

### Buttons:
- Primary: Neon pink fill, white text, pink glow
- Secondary: Transparent with cyan border, cyan glow on hover
- Danger: Hot red with pulsing glow
- "Power up" clip-path animation on hover

### Badges/Status:
- Pending: Electric yellow, pulsing
- Completed: Radioactive green, static glow
- Failed: Hot red, subtle flicker
- Holographic shine sweep animation

### Input Fields:
- Dark inset with subtle inner shadow
- Cyan border on focus with spreading glow
- Monospace font for terminal feel

### Chat Bubbles:
- Warden: Pink accent border left, dark glass fill
- User: Cyan accent border right
- Timestamps in dim monospace
- Glitch-flicker on new messages

---

## Animations & Effects

### Page Load Sequence:
1. Screen "boots up" - scanlines intensify then fade
2. Grid background fades in from center
3. Rain particles begin falling
4. Neon glows pulse once (power surge)
5. UI elements stagger in with glitch-flicker (50ms delays)
6. Metric numbers count up from zero

### Hover Effects:
- Cards: Border glow intensifies, 2px lift
- Nav items: Neon underline slides in, icon pulses
- Buttons: "Power charge" sweep animation

### Micro-interactions:
- Checkboxes: Cyber confirmation flash
- Toggles: Neon trail follows switch
- Dropdowns: Cascading stagger
- Toasts: Glitch-in from right, scan-line wipe out

### Glitch Effects (sparingly):
- Logo hover: RGB split + position jitter (100ms)
- Error states: Text flicker with offset copies
- Section transitions: Horizontal tear/reassemble

### Ambient/Passive:
- Rain: Continuous randomized thin streaks
- Neon glows: Slow pulse (8s cycle)
- Active metric: Subtle value shimmer
- "System online" dot: Breathing pulse

### Performance:
- All CSS-only (GPU accelerated)
- Rain uses CSS, not canvas
- Reduced motion media query respected

---

## Page Designs

### COMMAND (Dashboard):
- Top: 4 metric cards, hexagonal corners, glowing values
- Left (2/3): "RECENT OPS" feed + "ACTIVE PATTERNS"
- Right (1/3): "STREAK STATUS" arcs + "SYSTEM STATUS"

### COMMS (Chat):
- Full-height chat, messages floating in void
- Warden avatar: Glowing pink geometric
- User avatar: Cyan wireframe
- Collapsible side panel: Memory + Agent Intel

### MISSIONS (Commitments):
- Quick-add bar pinned top
- Terminal toggle tabs: [PENDING] [COMPLETE] [FAILED]
- Status indicator lights (glowing dots)
- Countdown format for close deadlines

### OBJECTIVES (Goals):
- Card per goal with animated progress bar
- Target date as holographic stamp
- Linked commitments mini-list

### TEMPORAL (Calendar):
- Vertical timeline with glowing markers
- Events as attached cards
- Pink (commitments) vs Cyan (calendar events)
- Pulsing "TODAY" marker

### SYSTEMS (Settings):
- Tabbed: CONFIG | SCHEDULES | INTEGRATIONS | ERRORS
- Setting groups in cards
- Error log with severity borders, expandable traces

---

## Implementation Notes

- Single-file HTML dashboard (dashboard_html.py)
- All fonts from Google Fonts
- CSS-only animations for performance
- Respect prefers-reduced-motion
- Mobile responsive with collapsible rail
