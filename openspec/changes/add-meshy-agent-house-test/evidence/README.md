# Evidence: add-meshy-agent-house-test

Test scenario: `meshy-agent-house` (`harness/scenarios/meshy_house.py`), fixture `base`. Both runs show the same camera view (the camera does not follow the moved pawn while the game is paused, so the view is not centred on the new house).

| File | Run id | Pak | Shows |
|---|---|---|---|
| `pak_house_z3000.jpg` | 20261020-041549-7439 | meshyhouse | Row of level 1 cottages on the right: white, untextured Meshy house. |
| `pak_house_z600.jpg` | 20261020-041549-7439 | meshyhouse | Close view of one Meshy house: stands on the ground, not sunk or floating. |
| `vanilla_house_z3000.jpg` | 20261020-041739-4836 | none | Same view: vanilla thatched cottages. |
| `vanilla_house_z600.jpg` | 20261020-041739-4836 | none | Same close view, vanilla. |
