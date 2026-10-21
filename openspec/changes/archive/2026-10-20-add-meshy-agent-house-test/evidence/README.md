# Evidence: add-meshy-agent-house-test

Test scenario: `meshy-agent-house` (`harness/scenarios/meshy_house.py`), fixture `base`. The scenario waits until the new house mesh is visible (about 8 game days after the plot is built), then centres the camera on the new house and takes pictures. The pictures keep the "A New Message" banner of the game.

| File | Run id | Pak | Shows |
|---|---|---|---|
| `pak_house_z1500.jpg` | 20261020-191326-00b1 | meshyhouse | The new house in the middle (cream plaster, black beams, tan thatch roof). The older replaced cottages stand in a row on the right. It stands on the ground. |
| `pak_house_z600.jpg` | 20261020-191326-00b1 | meshyhouse | Close view of the new house. |
| `pak_house_side_a.jpg` | 20261020-191326-00b1 | meshyhouse | The new house from the side (camera turned 90 degrees against the actor yaw). It stands on the ground. |
| `pak_house_side_b.jpg` | 20261020-191326-00b1 | meshyhouse | The same house from the other side (180 degrees). |
| `vanilla_house_z1500.jpg` | 20261020-060520-4786 | none | Vanilla: the same plot, a thatched cottage (this run centred the camera less well). |
| `vanilla_house_side_a.jpg` | 20261020-060520-4786 | none | Vanilla house from the side. |

Verdict: the house draws the Meshy texture (cream plaster, black beams, tan thatch). The cause of the old pale look was static switch overrides on the material instance; see `notes/import.md`, section "FIX".

Master swap test (2026-10-20): parent `MegascansStandard` (runs `20261020-162700-401e`, `20261020-163127-2b75`). The house stayed white and grey, so these pictures were not kept and the pak above is unchanged. See `notes/swap-shrines.md`.
