# Evidence: add-meshy-agent-house-test

Test scenario: `meshy-agent-house` (`harness/scenarios/meshy_house.py`), fixture `base`. The scenario waits until the new house mesh is visible (about 8 game days after the plot is built), then centres the camera on the new house and takes pictures. The pictures keep the "A New Message" banner of the game.

| File | Run id | Pak | Shows |
|---|---|---|---|
| `pak_house_z1500.jpg` | 20261020-061038-904c | meshyhouse | The new house in the middle (light walls, black beams, dark roof). The older replaced cottages stand in a row on the right. It stands on the ground. |
| `pak_house_z600.jpg` | 20261020-061038-904c | meshyhouse | Close view of the new house. |
| `pak_house_side_a.jpg` | 20261020-061038-904c | meshyhouse | The new house from the side (camera turned 90 degrees against the actor yaw). It stands on the ground. |
| `pak_house_side_b.jpg` | 20261020-061038-904c | meshyhouse | The same house from the other side (180 degrees). |
| `vanilla_house_z1500.jpg` | 20261020-060520-4786 | none | Vanilla: the same plot, a thatched cottage (this run centred the camera less well). |
| `vanilla_house_side_a.jpg` | 20261020-060520-4786 | none | Vanilla house from the side. |

Verdict: the house is drawn with the Meshy texture (black beams, cream plaster, dark roof) but it is pale. The brown wood and brown thatch of the Meshy texture do not show. See `notes/import.md`, section "White house".
