# Top bar check (task 4.2)

Run `ord-h-193058`. Picture `evidence/o3-top-bar-77.jpg`.

## Verdict

**The top bar percentage shows the value that the mod writes, for the region under the camera, while the game runs and the mod writes each tick.** A single write while the game is paused does not show.

## Numbers

- Camera over the village Riesenbuckel (Nusslohe), game running at speed 1, `Region.publicOrder = 77` written every 0.25 s for 12 s: the top bar read **77%** (`o3-top-bar-77.jpg`). Before the writes it read 42% (the game value 42).
- Camera over a free region (Kleine Nolle, region `selbitz`): the bar stayed 19% in two pictures while the village value was 77. The bar follows the region under the camera. The camera drifts (cursor near an edge), so check the region name in the bar.
- Paused, one write of 77: the bar read 19% (picture taken in the free region) and a text widget `OrderNumeric` (in `W_HUD_RegionStats_Right`, not the top bar) read "77%". So a write needs running ticks to reach the bar; a paused picture shows the old value.
- A text readout of `OrderNumeric` after short running periods with writes of 100, 77, 30 and 90 gave 100%, 77%, 30% and 90%. A write of 50 read "0%" (a transient sample, the known 0 and 100 jumps of #403).

## What this means

The mod value reaches the top bar (the number the player sees), and the tooltip shows its own list of factors. The two are independent: the tooltip sum (for example -50%) is not the bar value (for example 77%). The follow-up design must say what the rows add up to.

## Not verified

The bar with a per-tick write at speed 3; the bar for several owned regions.
