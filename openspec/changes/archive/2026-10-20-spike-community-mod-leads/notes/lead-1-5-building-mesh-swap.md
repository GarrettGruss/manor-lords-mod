# Lead 1.5: building mesh swap

Probe: test scenario `probe-lead-mesh` (default fixture, slot 0). Commands `lead_mesh_list`, `lead_mesh_swap`.

## Result (run 20261021-043848-a321; first good swap in run 20261021-043737-0402)
- `StaticMeshComponent:SetStaticMesh` works on a finished building and the picture changes at once. Target: the wooden bridge `SMBuilding` at (873, 24159), component `StaticMeshComponent0`. Mesh before: `/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_WoodenBridgeWide`. After: `/Game/UWG/3D/singpost`. Screenshots: `evidence/mesh-before.jpg` (bridge) and `evidence/mesh-after.jpg` (a sign post on a small platform).
- The new mesh was found with `StaticFindObject` (`loaded_with` "StaticFindObject"), because it was already loaded. `LoadAsset_Blocking` was not needed and not tested. Pak assets need the asset registry (see `load_pak_blueprint`), not `LoadAsset`.
- Restore works: `SetStaticMesh` with the saved mesh object gave the old path back and the old shapes (22 convex).
- Collision: the component flag `GetCollisionEnabled` stayed 1. The collision shape follows the mesh. The mesh body setup held 22 convex shapes before and 0 after (the sign post has no collision), and 22 again after the restore. So the swap gives the building the collision of the new mesh. A replacement mesh needs its own collision. A test that walks a unit into the building was not made.
- A building also has a `socketMesh` component (collision flag 3). Swap only `StaticMeshComponent0`.
- The socket count (`GetAllSocketNames`) and the bounds read gave nothing (`sockets` and `extent` missing). The probe did not pass a Lua string to an FName argument.

## Bugs fixed on the way
- `parseRequest` of `HarnessActions` had no fields `component`, `mesh`, `stance` and `restore` (run 20261021-043549-86f3 refused the swap).
- `GetPathName` gave nothing on a mesh; `GetFullName` ("StaticMesh <path>") works.

## Risks
- Only 60 building mesh components are listed (cap).
- What a save and load does with a swapped mesh was not checked (no save is allowed in a probe). The building class may set its own mesh again on load.
- Navigation and placement rules were not checked.

## Does a mod feature need it?
Yes, for a visual change of a finished building (a damaged or burnt look, a camp upgrade) without a new blueprint. Give the new mesh its own collision. Keep the commands.
