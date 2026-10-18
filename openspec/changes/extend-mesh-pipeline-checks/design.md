# Design: Extend mesh pipeline checks

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Does a Meshy mesh change the frame time? | A spike | Task 1.1 |
| What `spec` and `AO` values look right next to game textures? | The user (looks) | Task 2.1: pictures with 2 or 3 variants |
| Are UV and normal conventions right in UE 5.5.4? | A spike | Task 2.2: look at the pictures; fix in `meshy_material.py` if the normal map is inverted |
| Does a prop part need collision? | A spike | Task 2.3 |
| Which Python parts can be tested without Unreal or the network? | The implementer | Task 3.1 |
