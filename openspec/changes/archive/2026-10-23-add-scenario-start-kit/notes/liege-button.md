# The button on the liege screen (task 1.4)

The liege widget `WBP_LiegeTribute` (`mod/InvasionMod/ue/make_liege_widget.py`) is a cooked Widget Blueprint with Borders for buttons.
A new button needs a new Border (`ArmsButton`) and a text block (`ArmsInfoText`), so the widget is rebuilt and the pak `raidmenu` is rebuilt.
`HarnessClickHooks` has no enable switch. The button is disabled in two ways: the label and the info text show the reason, and the
click handler refuses the click (the same rule as the delivery).
