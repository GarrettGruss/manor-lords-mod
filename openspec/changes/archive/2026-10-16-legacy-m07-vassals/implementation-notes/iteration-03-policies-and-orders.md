# M07 iteration 03: notes

- Policies are three presets of two numbers each. A new policy is a config entry; the code reads `config.vassals.policies`.
- The loyalty tick and the tribute tick are separate polls on the same season change. Their order is not fixed, so a tribute can use the loyalty from before or after the tick. The tests check the share against the loyalty the payment reports.
- Loyalty only moves by policy and gift for now. Protection and raids change it in M08.02 and M07.04.
- Tribute with a heavy policy at loyalty 45 pays 29 goods for 5 families (rounded). Light at loyalty 48 pays 10.
