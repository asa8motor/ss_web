# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Personal portfolio website for visual/3D artist "sasha svoloch". Single-file, no build step — everything is in `claudemain.html`. `svg.html` is a staging file for updated SVG text layers exported from Figma.

## Development

Open `claudemain.html` directly in a browser — no server, no build, no npm. To preview changes, just refresh the browser.

### Figma image export (`script/script.py`)

Downloads all image nodes from a Figma file at 4× scale via the Figma REST API.

```bash
pip install requests
python script/script.py
```

Configure at the top of the file before running:

| Variable | Description |
|---|---|
| `TOKEN` | Figma personal access token (Settings → Security) |
| `FILE_KEY` | From the Figma file URL: `figma.com/file/FILE_KEY/...` |
| `SCALE` | Export scale, max 4 |
| `FORMAT` | `png` / `jpg` / `svg` / `pdf` |
| `OUT_DIR` | Output folder (default: `figma_images/`) |

The script walks the Figma document tree, finds nodes of type `IMAGE` or shapes with image fills, then fetches download URLs in batches of 100 and saves them locally.

## Architecture

### Layout system

The design is based on a **414px Figma mobile frame** scaled to fill the viewport:

- `--unit` (CSS var, computed in JS) = `(viewportWidth - gap*2) / 414`  
- Desktop gap: 350px each side. Mobile gap: 15px.
- All elements: `left: calc(N * var(--unit))`, `width: calc(N * var(--unit))` where N is the Figma pixel value.
- `--unit-scale` = same numeric value as `--unit` but without `px` — used for `transform: scale()`.

### Two rendering layers (both inside `#scale-wrapper`)

1. **Image/video layer** — `z-index: 10`, `position: absolute`, `left: 0; top: 0`. Contains all `<img>` and `<video>` elements plus interactive buttons, positioned with `calc(N * var(--unit))`.

2. **SVG text layer** (`#svg-text-layer`) — `z-index: 30`, `position: absolute`, `top: calc(136 * var(--unit))`, `left: 0`. Contains a single large SVG (exported from Figma) with all decorative vector text. Uses `transform: scale(var(--unit-scale))` with `transform-origin: top left` to scale Figma-px coordinates to screen pixels.
   - The inner container div is **394px wide** (not 414) — this centers the SVG content and gives ~10px margins matching the image layer's `left: calc(11 * var(--unit))` baseline.

### SVG text layer workflow

When Figma produces an updated SVG export, it goes into `svg.html`. To apply it to the main file, replace the content between the `<!-- НАЧИНАЙ -->` and `<!-- ЗАКОНЧИ -->` comments in `claudemain.html` — specifically the inner `<div style="width: 394px...">` block. Update the CSS `#svg-text-layer { height: ... }` to match the new SVG height.

### LORE window system

A single floating popup (`#lore-window`) shared by all interactive dots. Key mechanics:

- **Opening**: each `lore-dot-N` button and `#avatar-btn` loads a different text array into `loreData`, then calls `openWindow(sourceEl)`. Position is computed relative to the source element — opens right if source is on left half, left if on right half.
- **Height**: `max-height: calc(190 * var(--unit) * var(--lore-scale))` caps all windows uniformly. Short text → window shrinks to content. Long text → fixed height with scroll.
- **Text animation**: `startDecryptor()` renders all lines as invisible spans first (to measure layout height), then animates each line with a glitch/typewriter effect via `typeWriterLine()`.
- **`--lore-scale`**: `1.0` on desktop, `2.2` on mobile — scales the window and its font size.
- **`loreSets`** object: maps `lore-dot-N` IDs to text arrays. Adding a new lore dot requires: (1) a `<button id="lore-dot-N">` in the image layer, (2) an entry in `loreSets`.

### Fictional universe / lore content

The site's content references a sci-fi universe ("SP-2"). Characters: **E-V/LN (Evelyn)** — android protagonist; **Cade-0** — last human. The `text` file contains a short lore fragment used for `lore-dot-6`.

## Key IDs and elements

| ID | Purpose |
|---|---|
| `scale-wrapper` | Main canvas, all positioned content lives here |
| `svg-text-layer` | Scaled SVG vector text overlay |
| `lore-window` | Shared LORE popup |
| `lore-btn` | Primary LORE trigger (top of page) |
| `lore-dot-1` … `lore-dot-6` | Per-project info dots |
| `avatar-btn` | Logo image, opens intro text in LORE window |
| `scroll-to-top-btn` | Triangle SVG at bottom of canvas |
| `contact-overlay` | Fullscreen contacts modal |
| `fixed-footer` | Fixed "contact \| try it" bar |
