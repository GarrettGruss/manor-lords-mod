# Spec Delta

## Purpose

PolicyMenu is a standalone player mod. It adds a menu with all policies that the village can sign, and the player signs or unsigns a policy with a click.

## ADDED Requirements

### Requirement: F7 opens and closes the menu
The mod SHALL open the policy menu with the key F7 (setting `toggle_key`) and close it with the same key. The key callback SHALL only set a flag. The game thread tick SHALL do the toggle, so the game keeps answering.

#### Scenario: The real F7 key
- **WHEN** the player presses F7 while the menu is open and again after it is closed
- **THEN** the menu closes and then opens
- Checked by `harness/scenarios/policy_menu.py`.

### Requirement: The menu lists the available policies
The menu SHALL list every policy that the player region can sign now (up to 20), in the order of the policy id, with the name from the game. A signed policy has the mark "[x]" and a green button. An unsigned policy has the mark "[ ]" and a grey button. The menu reads the policy state every `refresh_ms` (default 1000 ms), so it follows changes made outside the menu.

#### Scenario: The menu shows policies with game names
- **WHEN** the player opens the menu
- **THEN** the menu is in the viewport and lists at least 1 policy
- **AND** no policy has the fallback name "Policy N"
- Checked by `harness/scenarios/policy_menu.py`.

### Requirement: A click signs or unsigns a policy
The mod SHALL sign an unsigned policy when the player clicks its button, and SHALL unsign a signed policy on the next click. A click is a press that ends while the mouse is on the button. A second click on the same button within `click_cooldown_s` (default 0.4 s) is ignored. The mod calls the game rule `setPolicySigned`. The result of a refused change is logged and shown in `last_error`.

#### Scenario: Two real clicks
- **WHEN** the player clicks the first policy button, and then clicks it again
- **THEN** the first click adds the policy id to the signed policies of the region and the menu shows it as signed
- **AND** the second click removes it
- Checked by `harness/scenarios/policy_menu.py`.

### Requirement: The menu is a pak widget
The mod SHALL show the menu as a Widget Blueprint from the pak `policymenu_P.pak`. If the pak is missing, the open call SHALL return `ok` false with a message that names the pak.

#### Scenario: The pak is loaded
- **WHEN** the scenario runs with the pak `policymenu`
- **THEN** the open command returns `ok` true
- Checked by `harness/scenarios/policy_menu.py`.

#### Scenario: The pak is missing
- **WHEN** the menu is opened without the pak
- **THEN** the answer has `ok` false and a message
- Not checked yet.

### Requirement: The mod needs only ManorCore
The mod SHALL load with the shared module ManorCore only. It SHALL NOT call a save function and SHALL NOT use eval. With the harness registry it SHALL register the commands `PolicyMenu.open`, `close`, `toggle` and `read` and the metrics `open`, `clicks` and `entries`.

#### Scenario: The commands are registered
- **WHEN** the mod loads with the harness
- **THEN** the scenario can open, read and close the menu by name
- Checked by `harness/scenarios/policy_menu.py`.

### Requirement: The mod is releasable
The mod SHALL ship with a manifest (`mod.json`), a changelog and its pak, and SHALL name `policy-menu` as its release gate scenario. The same holds for RefugeeWaves with the gate `refugee-wave`.

#### Scenario: The manifest names the gate
- **WHEN** the release tool reads `mod/PolicyMenu/mod.json`
- **THEN** the manifest lists the pak `policymenu` and the gate scenario `policy-menu`
- Not checked yet.
