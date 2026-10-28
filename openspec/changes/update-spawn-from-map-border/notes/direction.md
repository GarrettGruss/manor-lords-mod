# The compass of the direction notice

The notice says "Raiders approach from the west". The word comes from the border point seen from the manor (8 words, 45 degree sectors, `border.direction`).

The compass is an assumption: north is -y and east is +x (the usual top-down map of an Unreal level: image right is +x, image down is +y). It is not verified in the game: no compass or map orientation was read. The config key `invasion.border.north_axis` ("-y" or "+y") turns the words if the owner sees that the north is wrong.

How to check: in a game, read a notice and look where the raiders come in. The army enters at the west edge when the notice says west. Compare with the minimap of the game. Run `20261028-030011-b782` shows the notice "Raiders approach from the west" and the army at the west edge (x -92459) in the pictures of the evidence folder.
