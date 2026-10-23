#!/usr/bin/env bash
# Generate the narrator anchor panels (S10, S17, S19). S10 is made first and is the
# character and room reference for S17 and S19, so the three shots match.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
OUT=runs/storyboard/invasion-mod
mkdir -p "$OUT"
HUS=design/trailer/references/wikipedia/Jan_Hus_at_the_Stake.jpg

STYLE='A wide 16:9 landscape storybook panel in the drawing style of the attached late medieval Bohemian manuscript illumination: hand-drawn black ink outlines, flat mineral colors, visible parchment texture, slightly uneven hand-painted fills. Palette limited to near-black, bone white, ember orange and dried-blood red. Very dark, low-key light from one small hearth fire. No text, no letters, no labels. Use the attached manuscript only for drawing style and palette; do not copy any figure from it.'
NARRATOR='The narrator: a tired Franconian lord of about forty, short dark beard with some grey, hair to the neck, a plain dark-green wool coat over a mail shirt, a leather belt, no crown, no heraldry, no jewelry.'
ROOM='The room: the inside of a burned peasant house at night. Charred roof beams, part of the roof open to a dark sky, one wall broken through, soot on the walls, a small hearth fire as the only light. A rough wooden table with a single candle stub and a clay cup.'
SAME='The attached storybook panel shows this exact man and this exact room: keep his face, beard, clothes and the room the same.'

export GEMINI_API_KEY="$(powershell.exe -NoProfile -Command '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")' 2>/dev/null | tr -d '\r')"
[ -n "$GEMINI_API_KEY" ] || { echo "GEMINI_API_KEY not found in the Windows user environment" >&2; exit 1; }

shot() {
  local id="$1" prompt="$2"; shift 2
  local refs=()
  for ref in "$@"; do refs+=(--ref "$ref"); done
  if [ -f "$OUT/$id.png" ]; then echo "$id exists, skipped"; return; fi
  uv run python harness/tools/genimage.py --prompt "$STYLE $NARRATOR $ROOM $prompt" "${refs[@]}" --out "$OUT/$id.png" | tail -1
}

shot S10 'Shot: wide. The narrator sits alone at the table, seen from the side, his eyes down, his hands resting on the table. The broken wall and the open roof frame him. He looks small in the ruined room.' "$HUS"
shot S17 "Shot: medium, slightly closer than before. The narrator sits very still at the table, his face half in shadow, his eyes fixed on a sheathed sword that lies on the table under his right hand. $SAME" "$HUS" "$OUT/S10.png"
shot S19 "Shot: a closer, low camera, from slightly below the table edge. The narrator is now STANDING upright beside the table, his chair knocked back behind him. He holds the sheathed sword in his left hand, gripping the hilt with his right, ready to buckle it on. Only the hearth light from below falls on his face; the rest of the room is almost black. His expression is hard and decided. Show him from the knees up, filling the right half of the frame. $SAME" "$HUS" "$OUT/S10.png"
ls -la "$OUT"/S10.png "$OUT"/S17.png "$OUT"/S19.png
