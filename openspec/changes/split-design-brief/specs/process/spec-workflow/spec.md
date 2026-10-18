# Spec Delta

## MODIFIED Requirements

<!-- Issue: #292 -->

### Requirement: The game design stays with the user
The game design of the Invasion Mod SHALL live in `design/mod/`, outside `openspec/`: `invasion-mod.md` (the guiding philosophy), `decisions.md` (the decision log, with stable numbers) and `trailer.md`. `design/harness/` SHALL stay reserved for a harness design. The user owns it. A change SHALL only read it as source material, unless the user asks for a design change. `openspec/config.yaml` SHALL carry a short summary of the vision and the pillars, so every planning request sees them.

#### Scenario: A change uses a design rule
- **WHEN** a mod change needs a player rule from the design
- **THEN** the proposal cites the section of `design/mod/invasion-mod.md` or the decision number in `design/mod/decisions.md`
- **AND** the design files are not changed by the change
- Checked by review.

#### Scenario: A proposal against a pillar
- **WHEN** a mod proposal would contradict a design pillar
- **THEN** the agent stops and asks the user before the proposal goes to review
- Checked by review.

#### Scenario: A new decision
- **WHEN** the user makes a new design decision
- **THEN** it is added at the end of `design/mod/decisions.md` with the next number, and older numbers do not change
- Checked by review.
