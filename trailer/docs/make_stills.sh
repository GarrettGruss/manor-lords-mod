#!/usr/bin/env bash
# Make the final scene stills (task 2.2) from the approved style preamble and identity blocks.
# Masters: assets/images/scenes/<id>.png (git-ignored). Posters: <id>.webp (in git).
# A still whose PNG exists is skipped; delete the PNG to remake it.
set -euo pipefail
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$PROJECT/.." && pwd)"
cd "$REPO"
SCENES="$PROJECT/assets/images/scenes"
WIKI=design/trailer/references/wikipedia
HUS="$WIKI/Jan_Hus_at_the_Stake.jpg"
BATTLE="$WIKI/Hussitenkriege.tif.jpg"
BANNERS=openspec/changes/add-invasion-trailer/references/banners.png
STYLE="$(cat "$PROJECT/prompts/style-preamble.txt")"

NARRATOR='The narrator: an original figure, a tired Franconian lord of about forty, short dark beard with some grey, dark hair to the neck, a lined, honest face, a plain dark-green wool coat over a mail shirt, a brown leather belt, dark hose, worn boots, no crown, no heraldry, no jewelry.'
HOUSE='The room: the inside of a burned peasant house at night, charred roof beams, part of the roof open to a dark sky, one wall broken through, soot on the walls, a small hearth fire on the right as the only light, a rough wooden table with a candle stub and a clay cup. The room is very dark; most of the frame is near-black.'
HUSSITES='The Hussites: commoners, men and some women, in padded coats and hooded cloaks of brown, grey and undyed wool, kettle hats, a little mail, no full plate, no crosses or emblems on their clothes; flails, war hammers, spears, tall painted pavise shields.'
BANNER='The Hussite banner: a tall, narrow cloth banner hanging from a crossbar on a long pole, with a swallowtail end, a gold chalice (cup, stem, one round knob, wide foot, no gems) on a red field, exactly as in the attached banner sheet.'
SAME='The attached panel shows this exact man and this exact room: keep his face, beard, clothes and the room the same.'

export GEMINI_API_KEY="$(powershell.exe -NoProfile -Command '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")' 2>/dev/null | tr -d '\r')"
[ -n "$GEMINI_API_KEY" ] || { echo "GEMINI_API_KEY not found in the Windows user environment" >&2; exit 1; }

still() {
  local id="$1" prompt="$2"; shift 2
  local refs=()
  for ref in "$@"; do refs+=(--ref "$ref"); done
  if [ -f "$SCENES/$id.png" ]; then echo "$id exists, skipped"; return; fi
  uv run python harness/tools/genimage.py --prompt "$STYLE $prompt" "${refs[@]}" --out "$SCENES/$id.png" | tail -1
}

still 08-burned-house "$NARRATOR $HOUSE Shot: wide. He sits alone at the table, seen from the side, eyes down, hands resting on the table. The broken wall and the open roof frame him; he looks small in the ruined room. Leave the left third of the frame dark and empty." "$HUS"
still 10-still "$NARRATOR $HOUSE Shot: a medium close-up, much closer than a wide shot: his head, shoulders and hands fill the right half of the frame. He sits very still, his face half in shadow, his eyes fixed on a plain sheathed sword under his right hand on the table. $SAME" "$HUS" "$SCENES/08-burned-house.png"
still 12-turn "$NARRATOR $HOUSE Shot: a low camera from below the table edge. He stands upright beside the table, his chair knocked back, gripping the hilt of the sheathed sword, ready to buckle it on. Hearth light from below on his face, the rest near-black. A hard, decided expression. Knees up, right half of the frame. He is alone in the room: no other people, no scrolls, no horses. $SAME" "$SCENES/08-burned-house.png"
still 01-flint "Shot: almost total darkness. In the center, two hands strike a flint against steel; sparks light a pitch-soaked torch that just catches fire. The flame is the only light and shows only the hands and the torch head. Everything else is black." "$HUS"
still 02-torch "Shot: a burning torch falls from a hand toward a heap of straw and firewood at the foot of a wooden stake; only the lower part of the stake is visible. The torch is in mid-air, its flame streaming; the first sparks touch the straw. Black night; nothing else in the frame: no people, no scrolls, no banners, no patterned background." "$SCENES/08-burned-house.png"
still 04-given-word "Shot: a gloved hand holds a folded letter with a round red wax seal, a single-headed black eagle with spread wings on a gold field, over dark, still river water at night. The seal is reflected in the black water. Only the hand is visible. Cold and threatening. Leave the right third of the frame dark." "$HUS" "$BANNERS"
still 05-answer "$HUSSITES Shot: a village forge at night. Men and women hammer farm flails and scythe blades into weapons on an anvil. In the foreground, large and sharp, one iron-bound flail head lies across the anvil under a raised hammer. A glowing forge is the warm light. On the wall behind hangs one small red cloth with a gold chalice. Determined faces. No shields, no crosses and no emblems anywhere except the one chalice cloth. Leave the left third calmer and darker." "$SCENES/08-burned-house.png" "$BANNERS"
still 06-banner "$HUSSITES $BANNER Shot: on a low hill, a ring of heavy wooden farm wagons with high plank sides, chained wheel to wheel, forms a fort. A captain in a kettle hat and padded coat stands on a wagon and raises the banner high; the banner is the tallest thing in the frame, its swallowtail end hanging below the crossbar. Hussites with flails and pavise shields behind the wagons. Dark red sky at dusk." "$BATTLE" "$BANNERS"
still 14-map "Shot: a hand-painted medieval parchment map seen from above: a river valley with forests, small walled towns drawn as tiny clusters, and roads. From the right edge, a long dark column of a marching army, drawn as rows of tiny figures under tall red banners with gold chalices, moves along a road toward one walled town on the left. Burn marks at the parchment edges. No place names, no text." "$BATTLE" "$BANNERS"
still 16-title "Shot: an empty sheet of old parchment filling the frame, its edges burning with small ember-orange flames and black char that curls inward. Smoke and drifting embers at the edges. The center is plain, empty and slightly darker, left free for a title. No text, no letters, no symbols." "$HUS"

# Regrade the two public domain Jena Codex pages: palette toward black, bone, ember and blood red, on a dark parchment field.
regrade() {
  local id="$1" source="$2"
  if [ -f "$SCENES/$id.png" ]; then echo "$id exists, skipped"; return; fi
  ffmpeg -loglevel error -y -f lavfi -i "color=c=0x1a120c:s=1920x1080" -i "$source" -filter_complex \
    "[1:v]scale=-2:1000,eq=saturation=0.75:contrast=1.15:brightness=-0.06,colorbalance=rs=0.08:gs=-0.06:bs=-0.10:rm=0.06:gm=-0.04:bm=-0.08[page];[0:v][page]overlay=(W-w)/2:(H-h)/2" \
    -frames:v 1 "$SCENES/$id.png"
  echo "regraded $id"
}
regrade 03-stake "$HUS"
regrade 07-red-sky "$BATTLE"

for png in "$SCENES"/*.png; do
  webp="${png%.png}.webp"
  [ -f "$webp" ] && [ "$webp" -nt "$png" ] && continue
  ffmpeg -loglevel error -y -i "$png" -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black" -quality 80 "$webp"
done
ls "$SCENES"
