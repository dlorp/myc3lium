# EJ22-TRACKER: Interactive TUI Dashboard

**Session 5 Prototype** — Built a full TUI interface for Subaru maintenance tracking

## What It Is

Terminal dashboard for tracking '97-'99 Impreza EJ22 maintenance. Local-first, no cloud, built for solo garage wrenchers.

## What's New

### Before (CLI only):
```bash
$ ej22 next
Next Service Items (Current: 147,500 miles)
╭───────────────┬─────────┬────────────┬────────╮
│ Service       │  Due At │ Miles Left │ Status │
╰───────────────┴─────────┴────────────┴────────╯
```

### After (Interactive TUI):
```
╔═══════════════════════════════════════════════════════╗
║ EJ22-TRACKER          Subaru Maintenance Dashboard   ║
╠═══════════════════════════════════════════════════════╣
║  ┌─────────────────┐  ┌──────────────────────────┐  ║
║  │ VEHICLE INFO    │  │ SERVICE HISTORY         │  ║
║  │ 1997 Impreza    │  │ 2026-03-18  Oil Change  │  ║
║  │ EJ22 Engine     │  │   @ 147,500 mi          │  ║
║  │ 147,500 miles   │  │ 2026-03-18  Air Filter  │  ║
║  └─────────────────┘  │   @ 145,000 mi          │  ║
║                       │                          │  ║
║  ┌─────────────────┐  │ 2026-03-10  Spark Plugs │  ║
║  │ NEXT SERVICE    │  │   @ 142,000 mi          │  ║
║  │                 │  │                          │  ║
║  │ Coolant  2,500  │  │ 2026-02-28  Trans Fluid │  ║
║  │          🟢     │  │   @ 140,000 mi          │  ║
║  │ Oil      3,000  │  │                          │  ║
║  │          🟢     │  │ [scrollable history...] │  ║
║  └─────────────────┘  └──────────────────────────┘  ║
╠═══════════════════════════════════════════════════════╣
║ l Log  r Refresh  q Quit                            ║
╚═══════════════════════════════════════════════════════╝
```

Press `l` to log service:
```
┌─────────────────────┐
│   Log Service       │
│ ┌─────────────────┐ │
│ │ Oil Change      │ │  ← Service type
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ 150500          │ │  ← Mileage
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ Mobil1 5W-30   │ │  ← Notes
│ └─────────────────┘ │
│  [Save]  [Cancel]   │
└─────────────────────┘
```

## Features

- **PSX Aesthetic**: Blue/cyan palette from PS1 menus
- **Live Dashboard**: Mileage, next service, history at a glance
- **Quick Logging**: Press `l` from anywhere
- **Color-Coded**: 🟢 OK / 🟡 Soon / 🔴 Overdue
- **Keyboard-Only**: No mouse needed
- **Local-First**: JSON storage in `~/.ej22-tracker/`

## Tech Stack

- Python 3.8+
- `textual>=0.47.0` for TUI widgets
- `rich` for CLI fallback
- Modal screens + live refresh

## Use Case

For the wrencher who:
- Does their own oil changes
- Wants records without spreadsheets
- Needs quick reference under the hood
- Values terminal-native tools

## Installation

```bash
cd ~/repos/ej22-tracker
pip install -r requirements.txt
./ej22           # Launch TUI
./ej22 specs     # CLI mode
```

## Files

- `ej22_tui.py` - TUI application (11.5 KB)
- `ej22_tracker.py` - CLI version (16 KB)
- `ej22` - Unified launcher
- Data: `~/.ej22-tracker/*.json`

## Design Philosophy

**Constraints = Creativity**
- Terminal-only → Keyboard shortcuts
- No cloud → Local JSON files
- Solo wrencher → Quick reference focus
- PSX aesthetic → Blue/cyan minimalism

**Next Ideas**:
- Mileage graph (sparkline)
- OEM part lookup modal
- Export to PDF/markdown
- Integration with OBD2 diagnostics

---

**Commit**: `178ff31`  
**Time**: 35 minutes  
**Status**: Prototype complete, tested, documented
