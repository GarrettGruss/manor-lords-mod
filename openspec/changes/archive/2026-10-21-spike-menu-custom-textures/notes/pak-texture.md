# Pak texture (task 1.2): not done

Not run. Blockers:
- A cooked `Texture2D` needs the UE editor in `C:\Users\garre\development\mlm-ue\ManorLords` (import with `unreal.AssetImportTask`, then cook), as in `prep.md`. This needs a new editor script and a cook, then a pak build and one more real game run.
- The game run cap of this session (6 runs) was used on the runtime PNG probe and its harness fixes. The probe has no `load_asset` action for a pak texture yet.
- Next step: write the editor script (`make_test_texture.py`, pattern of `make_click_button.py`), cook, build the pak with `pakmod.py`, add a `load_asset` action to the probe, and run with `--pak`.
