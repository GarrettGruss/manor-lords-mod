# Evidence

No picture of a real hover yet. The tooltip property is proven by test scenario `tech-tree-widget-tooltip` (run `20261023-224700-0922`, checks T1 to T4: the text of the Border `ToolTipText` of each button equals the expected effect lines).

The real hover picture needs the owner: the OS mouse scan found no button (another game window covered the screen, and the game stopped answering for 10 s during the scan). Run `uv run python harness\run.py --scenario tech-tree-widget-tooltip --pak techmenu --slot 0` with the mouse connected and no other game window open. It writes `tech-tree-tooltip-node` and `tech-tree-tooltip-law` screenshots.
