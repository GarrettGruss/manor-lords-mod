# Generation (task 2.1, 2026-10-19)

Tool: `meshy` 0.4.3 (Pro account, MESHY_API_KEY from the owner's environment). Tasks stay private. Nothing was published.

## Prompt (text-to-3d preview)
"Medieval timber-frame peasant house, single storey, thatched steep roof, wattle and daub walls with dark oak beams, small door and window, low poly game asset, Manor Lords style, stylized hand-painted, no ground, no base"
Options: `--model-type smart-topology --target-polycount 3000 --target-formats glb,fbx`.
Refine texture prompt: "weathered oak beams, off-white plaster, brown thatch, muted medieval colors" (`--texture-resolution 2k`, PBR on).

## Tasks and credits
| Step | Task id | Credits |
|---|---|---|
| preview | `01a15757-6c43-7517-9bd4-2db10a910eb4` | 5 |
| refine (texture) | `01a15758-6d08-7539-a6f6-ff11f8f912fb` | 10 |

Balance before 1010, after 995 (15 credits, 2 generations). Each step took about 1 minute.

## Files (git-ignored, `runs/genmesh/meshy-agent-house/`)
`model.fbx` (12.8 MB, from the refine task), `model.glb`, `textures/texture_0_{base_color,metallic,normal,roughness}.png`.
The UE import script accepts FBX only, so the FBX was used. Imported mesh: 3210 vertices, one material.
