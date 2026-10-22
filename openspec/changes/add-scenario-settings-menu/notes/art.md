# Art: the look of the menu

The approved mockup (illuminated manuscript) could not be read as a page in this session (the artifact page is a design canvas that is not served as text).
The menu is built from the mockup description in the change: a title, a background text block, four rows with three buttons, two buttons.
Implemented look (`ue/make_scenario_settings_widget.py`): a parchment coloured panel (Border brush colour), dark brown text, the standard click button style of `WBP_ClickButton`
for choices and buttons, the chosen choice marked as `> Normal <`.
NOT done: the PNG images (frame, title banner, button art) of the mockup. A PNG loaded at run time (spike #333: `ImportFileAsTexture2D`, `SetBrushFromTexture`) needs the image files
from the owner or a generated set, and a part in `core/menu.lua` or the feature that sets brushes on the widget. Question for the owner: supply the PNG files, or accept the colour look
for now? The pictures for the evidence (task 4.3) need slot 0 and are not taken.
