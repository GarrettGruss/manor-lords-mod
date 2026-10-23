"""Single source for the trailer chapters (slow cut). Writes content/story.json,
content/timing.json and docs/storyboard.md, so the three never disagree.

Run from the project root: uv run python docs/chapters.py
Shot ids refer to design/trailer/invasion-mod/slow/05-shot-list.md.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONNECTOR_SECONDS = 0.5
TOTAL_SECONDS = 60.0

# (id, label, shots, shot seconds, look, focal subject, camera, copy position, copy, connector to the next chapter)
# Connector None means a hard cut, chosen on purpose (see docs/production-spec.md).
CHAPTERS = [
    ("00-darkness", "Darkness", "S01-S02", 5.0, "Black", "Nothing: full black", "None", "center",
     ["Christe, fili Dei vivi, miserere mei."], None),
    ("01-flint", "Flint", "S03", 1.5, "Manuscript", "Hands strike a flint; the torch catches", "Locked", "bottom",
     [], "The torch flame swings down and the camera follows it"),
    ("02-torch", "The torch falls", "S04", 1.5, "Manuscript", "The torch falls into the straw at the stake", "Follow the torch down", "bottom",
     [], "Flames erupt from the straw and fill the frame, then thin to show the stake"),
    ("03-stake", "Constance", "S05a-S05b", 4.0, "Manuscript", "Jan Hus at the stake, flames rising (Jena Codex page, regraded)", "Static, then tilt up", "right",
     [], "The flames darken to smoke and the smoke becomes black water"),
    ("04-given-word", "The given word", "S06-S06b", 5.0, "Black, then Manuscript", "Black; then the king's sealed letter over dark water", "Static", "left",
     ["Constance, in the year of our Lord fourteen fifteen.", "They gave him their word. Then they burned him."],
     "Sparks rise from the water and become sparks from a forge"),
    ("05-answer", "Bohemia answered", "S07", 2.0, "Manuscript", "Men and women beat flails into weapons at a forge", "Parallax", "left",
     ["Bohemia answered."], "The camera rises past the forge roof to a hill with a ring of wagons"),
    ("06-banner", "Four crusades", "S08", 2.5, "Manuscript", "A captain raises the chalice banner over a ring of war wagons", "Slow push-in", "right",
     ["Four crusades marched against them."], "The red sky behind the banner widens into the battle page"),
    ("07-red-sky", "Four crusades broke", "S09", 2.5, "Manuscript", "The Hussite army under a red sky (Jena Codex page, regraded)", "Parallax; the page edge burns", "left",
     ["Four crusades broke."], "The page burns away and shows a dark room behind it"),
    ("08-burned-house", "Franconia, 1429", "S10", 3.0, "Ember", "The narrator alone at a table in a burned house", "Static after the page burn", "right",
     ["Franconia, 1429."], "The camera moves through the broken wall into grey daylight and smoke"),
    ("09-raids", "The war comes", "S11-S16c", 12.0, "Ash (gameplay)", "Gameplay montage: raiders on the road, ransom and fire, looting, refugees and bandits, a barn burning", "Gameplay cuts inside the stage", "bottom",
     ["I did not choose this war.", "Then they rode west, into Franconia. Towns that paid were spared. Towns that would not, burned.",
      "And the hungry want bread. We marched on Bohemia. Now Bohemia marches on us."],
     "Smoke fills the frame and clears to the hearth in the burned house"),
    ("10-still", "He sits still", "S17", 2.5, "Ember", "The narrator, still, his hand on the sword", "Very slow push-in", "right",
     [], "The camera turns from the hearth to the doorway and the village beyond"),
    ("11-choice", "Fear or faith", "S18", 3.0, "Ash and Day (gameplay)", "Split frame: a gallows and a full market in the same village", "Static split frame", "center",
     ["Rule by fear, or by faith."], "The split closes into the dark house again"),
    ("12-turn", "He stands", "S19", 1.0, "Ember", "The narrator stands and takes the sword", "Static", "left",
     [], "He walks out of the house into daylight at the palisade gate"),
    ("13-battle", "The line holds", "S20-S26", 7.5, "Day (gameplay)", "The lord at the gate; the militia forms up; the lines meet; the raiders break and flee past their captain", "Gameplay cuts inside the stage", "bottom",
     [], "The camera rises from the field into cloud, and the cloud becomes parchment"),
    ("14-map", "The great raid", "S27", 2.5, "Manuscript", "The region map: a larger army marches on the town", "Slow crane down onto the map", "right",
     [], None),
    ("15-whisper", "Black", "S28", 1.5, "Black", "Nothing: full black", "None", "center",
     ["Restore order. Or burn with it."], None),
    ("16-title", "Title", "S29", 3.0, "Manuscript", "Burning parchment; the title is set as text", "Static; embers drift", "center",
     ["The Hussites Are Coming"], None),
]


def scene_seconds(shot_seconds, connector):
    """A connector takes its time from the end of the scene before it, so the cut stays on the shot list times."""
    return round(shot_seconds - (CONNECTOR_SECONDS if connector else 0.0), 2)


def build_story():
    chapters = []
    for index, (cid, label, shots, _secs, look, _focal, _camera, position, copy, _conn) in enumerate(CHAPTERS):
        chapters.append({
            "id": cid, "label": label, "eyebrow": f"{shots} · {look}", "title": label, "subtitle": shots,
            "copyPosition": position, "span": 4.6, "linger": 0.35, "paragraphs": copy, "tags": [look],
            "still": f"assets/images/scenes/{cid}.webp", "clip": f"assets/video/dives/{cid}.mp4",
        })
    connectors = [f"assets/video/connectors/{CHAPTERS[i][0]}-to-{CHAPTERS[i + 1][0]}.mp4" if CHAPTERS[i][9] else None
                  for i in range(len(CHAPTERS) - 1)]
    return {
        "meta": {
            "title": "The Hussites Are Coming",
            "kicker": "Invasion Mod for Manor Lords",
            "subtitle": "Franconia, 1429",
            "description": "The trailer of the Invasion Mod: Hussite raids into Franconia, 1429.",
            "note": "Slow cut. Shot ids refer to design/trailer/invasion-mod/slow/05-shot-list.md.",
            "style": "cinematic", "ui": "folio", "connectorSpan": 1.2,
        },
        "chapters": chapters,
        "connectors": connectors,
        "sources": [
            {"label": "Hussite Wars (Wikipedia)", "url": "https://en.wikipedia.org/wiki/Hussite_Wars"},
            {"label": "Jena Codex (National Museum, Prague)", "url": "https://muzeum3000.nm.cz/zajimavosti/jensky-kodex"},
        ],
    }


def build_timing():
    seconds = {}
    for index, chapter in enumerate(CHAPTERS):
        cid, shot_seconds, connector = chapter[0], chapter[3], chapter[9]
        seconds[cid] = scene_seconds(shot_seconds, connector)
        if connector:
            seconds[f"connector-{index}"] = CONNECTOR_SECONDS
    total = round(sum(seconds.values()), 2)
    if total != TOTAL_SECONDS:
        raise SystemExit(f"Chapters add up to {total} s, not {TOTAL_SECONDS} s")
    return {"width": 1920, "height": 1080, "fps": 30, "default_scene_seconds": 4,
            "default_connector_seconds": CONNECTOR_SECONDS, "seconds": seconds,
            "head_seconds": 0, "tail_seconds": 0}


def build_storyboard():
    rows = ["| # | Chapter | Shots | Start | Video s | Look | Focal subject | Camera | Copy position | Display copy | Connector to the next chapter |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    start = 0.0
    for index, (cid, label, shots, secs, look, focal, camera, position, copy, conn) in enumerate(CHAPTERS):
        text = " / ".join(copy) if copy else "—"
        rows.append(f"| {index} | `{cid}` {label} | {shots} | {int(start // 60)}:{start % 60:04.1f} | {secs} | {look} | {focal} | {camera} | {position} | {text} | {conn or 'Hard cut'} |")
        start += secs
    return "\n".join(rows) + "\n"


def write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


if __name__ == "__main__":
    write(ROOT / "content/story.json", json.dumps(build_story(), indent=2, ensure_ascii=False) + "\n")
    write(ROOT / "content/timing.json", json.dumps(build_timing(), indent=2) + "\n")
    board = ROOT / "docs/storyboard.md"
    text = board.read_text(encoding="utf-8")
    begin, end = "<!-- chapters:begin -->\n", "<!-- chapters:end -->"
    write(board, text[:text.index(begin) + len(begin)] + build_storyboard() + text[text.index(end):])
    print(f"{len(CHAPTERS)} chapters, {sum(1 for c in CHAPTERS[:-1] if c[9])} connectors, 60 s")
