# Proposal: Spike menu custom textures

Issue: #333.

## Why
The owner approved a new look for the tech tree menu (2026-10-20): the "Book of Charters", in the style of an illuminated manuscript. Mockup: https://claude.ai/artifact/DjmEqNN8frVzc9YF6UywPW (artboard "Charters, illuminated manuscript"). It needs custom pictures in the menu: a parchment background, a patterned border, framed cards and illuminated capital letters. It may also need a blackletter font.

The mod menus are game widgets made from a pak (`WBP_*`) and filled from Lua. Nobody has shown yet that a mod menu can show a picture that the game does not have. This spike finds out how, before a change for the new menu is written.

## What Changes
- Find a way to show a custom picture in a mod menu, and prove it with a real game run and a screenshot. Candidates (design.md):
  1. A texture cooked into a mod pak and set on an `Image` widget from Lua.
  2. A PNG file loaded at run time (`KismetRenderingLibrary:ImportFileAsTexture2D`) and set on an `Image` widget, with no pak.
  3. A widget blueprint in the pak that already holds the textures.
- Check that a frame picture can stretch without blurring its corners (9-slice, a brush drawn as Box or Border).
- Check whether a custom font (blackletter) can be used, or record that it cannot.
- Write the results to `notes/` and recommend one way.

## Non-goals
- Building the new tech tree menu. That is a later change, after this spike and the base menu of `add-mod-menu-access-rule` (#308).
- Final art. The spike uses test pictures.
- Changing game files or game paks.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None. A spike records findings only.

## Impact
- Real game runs, one at a time, single-player, no save call.
- A test pak and test PNG files under the change folder or `mod/`, only if the spike needs them. The pak AES key rules apply.
