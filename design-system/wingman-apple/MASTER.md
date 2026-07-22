# Wingman Apple-style desktop system

## Intent

Wingman is a focused scientific workbench, not a marketing page. The interface follows macOS desktop conventions through a unified toolbar, a persistent material sidebar, grouped settings, a clear results workspace, and restrained system colour. The existing `sv-ttk` package supplies production-tested widget assets and states.

## Layout

- Window: 1280 x 800 default, 1024 x 680 minimum.
- Toolbar: 60 px, product identity on the left, environment and language controls on the right.
- Sidebar: 276 px, method count, search, and hierarchical method navigation.
- Workspace: two top-level destinations, Setup and Results; analysis log remains a collapsible bottom drawer.
- Spacing uses an 8 px rhythm, with 12-18 px grouped-section padding.

## Tokens

| Role | Value |
|---|---|
| Window | `#F5F5F7` |
| Content | `#FFFFFF` |
| Toolbar | `#F6F6F8` |
| Sidebar | `#ECECF1` |
| Fill | `#E8E8ED` |
| Separator | `#D2D2D7` |
| Primary text | `#1D1D1F` |
| Secondary text | `#5F5F63` |
| System blue | `#007AFF` |
| Selection | `#DCEBFF` |
| Success / warning / error | `#248A3D` / `#C46A00` / `#FF3B30` |

Typography uses Segoe UI Variable Display/Text as the Windows system analogue to SF Pro, with Cascadia Mono for logs and technical values.

## Interaction rules

- Use `sv-ttk` widgets and `Accent.TButton`; do not hand-draw replacement controls.
- Preserve visible focus, disabled, hover, selected, progress, success, and error states.
- `Ctrl+F` focuses method search, `Ctrl+1/2` switches Setup/Results, and `Ctrl+L` toggles the log.
- Status colour always accompanies text or an explicit state label.
- Errors automatically reveal the log; successful runs move to Results.

## Guardrails

- No fake macOS traffic-light window controls.
- No decorative gradients, emoji icons, heavy blur, or low-contrast translucent text.
- Do not turn dense scientific forms into large marketing cards; progressive disclosure and readable tables take priority.
- Keep Bio Wingman and Meta Wingman shell styles synchronized.
