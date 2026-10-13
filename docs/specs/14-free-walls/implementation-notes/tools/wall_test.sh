#!/bin/bash
# One wall block test. Usage: RUN=<run> wall_test.sh <walls.json> <label> [bait=1]
# Spawns bait at "inside" (only when bait=1), clears bandits, spawns Brigands at "behind", checks the start, tracks 60 s at 1x, pauses.
cd /c/Users/garre/development/manor-lords-mod
S='C:/Users/garre/AppData/Local/Temp/claude/C--Users-garre-development-manor-lords-mod/3cd026e0-2eb0-4baf-b533-eb1e9f417e13/scratchpad'
PY=.venv/Scripts/python.exe
J=$1; LABEL=$2; BAIT=${3:-1}
offsets() {  # target x y -> dx dy from the pawn
  L=$($PY $S/bq.py call '{"ref":"first:MyPawnCPP_BP3_C","function":"K2_GetActorLocation","args":[]}' | tr -d '\n ')
  $PY -c "import json,sys; p=json.loads(sys.argv[1])['result']; print(round(float(sys.argv[2])-p['X']), round(float(sys.argv[3])-p['Y']))" "$L" "$1" "$2"
}
read IX IY BX BY < <($PY -c "import json,sys; d=json.load(open(sys.argv[1])); print(*d['inside'], *d['behind'])" "$J")
if [ "$BAIT" = "1" ]; then
  read DX DY < <(offsets $IX $IY)
  $PY $S/lc.py spawn_units side=player template=spearMilitia count=1 dx=$DX dy=$DY | grep -oE '"id": [0-9]+,' | head -1
fi
$PY $S/lc.py kill_units side=bandit count=200 | grep -o '"killed": [0-9]*'
read DX DY < <(offsets $BX $BY)
Q=$($PY $S/lc.py spawn_units side=bandit template=Brigands count=1 dx=$DX dy=$DY | grep -oE '"id": [0-9]+,' | grep -o '[0-9]*' | head -1)
POS=$($PY $S/squad_pos.py $Q)
echo "bandits $Q start $POS (target $BX $BY)"
$PY $S/lc.py path_state | grep -o '"obstacles": [0-9]*'
timeout 200 $PY $S/cross_watch.py "$J" $Q 60 1 > runs/$RUN/cross_$LABEL.jsonl 2>&1
$PY $S/bq.py call '{"ref":"first:MyPawnCPP_BP3_C","function":"changeGameSpeed","args":[0,false]}' >/dev/null
tail -1 runs/$RUN/cross_$LABEL.jsonl
