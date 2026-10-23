#!/usr/bin/env bash
# Generate the missing Manuscript storyboard panels. One Gemini call per shot.
set -euo pipefail
cd /home/garre/development/manor-lords-mod
OUT=runs/storyboard/invasion-mod
mkdir -p "$OUT"
WIKI=design/trailer/references/wikipedia
HUS="$WIKI/Jan_Hus_at_the_Stake.jpg"
BATTLE="$WIKI/Hussitenkriege.tif.jpg"
BANNERS=openspec/changes/add-invasion-trailer/references/banners.png

STYLE='A wide 16:9 landscape storybook panel in the drawing style of the attached late medieval Bohemian manuscript illuminations: hand-drawn black ink outlines, flat mineral colors, visible parchment texture, slightly uneven hand-painted fills. Palette limited to near-black, bone white, ember orange and dried-blood red, with a little gold. Dark, dramatic, low light. No text, no letters, no labels, no borders with writing. Use the attached images only for drawing style and palette; do not copy any figure or composition from them.'

export GEMINI_API_KEY="$(powershell.exe -NoProfile -Command '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")' 2>/dev/null | tr -d '\r')"
[ -n "$GEMINI_API_KEY" ] || { echo "GEMINI_API_KEY not found in the Windows user environment" >&2; exit 1; }

shot() {
  local id="$1" prompt="$2"; shift 2
  local refs=()
  for ref in "$@"; do refs+=(--ref "$ref"); done
  if [ -f "$OUT/$id.png" ]; then echo "$id exists, skipped"; return; fi
  uv run python harness/tools/genimage.py --prompt "$STYLE $prompt" "${refs[@]}" --out "$OUT/$id.png" | tail -1
}

shot S03 'Scene: almost total darkness. In the center, two hands strike a flint against steel; a shower of sparks lights a pitch-soaked torch that just catches fire. The flame is the only light; it shows only the hands and the torch head. Everything else is black.' "$HUS"
shot S04 'Scene: a burning torch falls from a hand toward a heap of straw and firewood at the foot of a wooden stake. Only the lower part of the stake is visible. The torch is in mid-air, its flame streaming; the first sparks touch the straw. Black night around it.' "$HUS"
shot S06b 'Scene: a folded letter with a round red wax seal, a single-headed black eagle on gold in the seal, held by a gloved hand over dark, still river water at night. The reflection of the seal shows in the black water. Cold and threatening, no people visible except the hand.' "$HUS" "$BANNERS"
shot S07 'Scene: a village forge at night. Bohemian peasants, both men and women, hammer farm flails and scythe blades into weapons on an anvil and on wooden blocks. They wear plain undyed or brown hooded cloaks, grey and brown tunics and simple caps. No crosses, no emblems and no symbols on any clothing. Iron-bound flail heads, sparks, a glowing forge as the warm light. On the wall behind them hangs one small red cloth with a gold chalice. Determined faces.' "$BATTLE" "$BANNERS"
shot S08 'Scene: on a low hill, a ring of heavy wooden war wagons chained together forms a fort. Above them, a captain in a kettle hat and padded coat raises a tall, narrow swallowtail banner: a gold chalice on a red field, exactly as in the attached banner sheet. Hussite foot soldiers with flails and pavise shields stand behind the wagons. Red sky at dusk.' "$BATTLE" "$BANNERS"
shot S27 'Scene: a hand-painted medieval parchment map seen from above: a river valley with forests, small fortified towns drawn as tiny walled clusters, and roads. From the right edge, a long dark mass of a marching army, drawn as rows of tiny figures and tall red banners with gold chalices, moves along a road toward one walled town on the left. Burn marks at the parchment edges. No place names, no text.' "$BATTLE" "$BANNERS"
shot S29 'Scene: an empty sheet of old parchment, filling the frame, its edges burning with small ember-orange flames and black char that curls inward. Smoke and drifting embers at the edges. The center is plain, empty, and slightly darker, left free for a title to be placed later. No text, no letters, no symbols in the center.' "$HUS"
ls -la "$OUT"
