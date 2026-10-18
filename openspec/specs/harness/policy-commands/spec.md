# harness/policy-commands Specification

## Purpose
Named harness commands that read and enact the policies (edicts) of the player region. Tests and mods use them to set a policy without the policy screen and to read the approval effect.

## Requirements

### Requirement: Policy state is read only
The harness SHALL answer `policy_state` with the policies in the slots, the signed ids, the available ids, the slot count, the approval with its factors, the silver, the influence and the population of the player region. `policy_state` SHALL NOT change the game.

#### Scenario: Read the state
- **WHEN** a client sends `policy_state`
- **THEN** the reply gives slots, available ids, approval, silver and influence
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: The read changes nothing
- **WHEN** a client sends `policy_state`
- **THEN** no policy is enacted and no game call writes a value
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

### Requirement: A policy is enacted with the game call
The harness SHALL enact a policy on `policy_enact` with `policy` (a whole number from 1 to 40) and `slot` (a whole number from 0 up to the slot count minus 1). It SHALL use the game call of the policy screen and answer with the state before and after and the value that the game returned. The harness SHALL refuse a policy that is not in the available list and a slot outside the slot count, without a game call.

#### Scenario: Enact an available policy
- **WHEN** a client sends `policy_enact` with an available policy id and slot 0
- **THEN** the reply is ok and has `before`, `after` and `returned`
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: A policy that is not available
- **WHEN** a client sends `policy_enact` with an id that is not in the available list
- **THEN** the reply is not ok and the game call is not made
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: A slot outside the count
- **WHEN** a client sends `policy_enact` with a slot at or above the slot count
- **THEN** the reply is not ok and the game call is not made
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: Bad input
- **WHEN** a client sends `policy_enact` with a policy id below 1 or above 40, or with no policy
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

### Requirement: A policy can be signed or unsigned
The harness SHALL set the signed state of a policy on `policy_sign` with `policy` (1 to 40) and `signed` (a boolean), with the call that the policy widget uses. The reply SHALL give the state before and after. The harness SHALL refuse a `signed` value that is not a boolean.

#### Scenario: Sign and unsign
- **WHEN** a client sends `policy_sign` with `signed` true and then false
- **THEN** the policy id is in the signed list after the first command and not after the second
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: A signed value that is not a boolean
- **WHEN** a client sends `policy_sign` with no `signed` value or a value that is not true or false
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

### Requirement: The policy sweep needs an explicit game setting
The harness SHALL refuse `policy_enact_sweep` unless the game runs with `HARNESS_ALLOW_UNSAFE=1`. The refusal SHALL name the variable. With the variable set, the sweep SHALL call the enact call for many ids and slots without a pre-check and stop at the first call that returns true.

#### Scenario: The variable is not set
- **WHEN** a client sends `policy_enact_sweep` and the game has no `HARNESS_ALLOW_UNSAFE=1`
- **THEN** the reply is not ok and the error contains `HARNESS_ALLOW_UNSAFE=1`
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: The sweep stops at the first true
- **WHEN** the variable is set and the game returns true for one id and slot
- **THEN** the sweep stops at that call and reports it as `first_true`
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

### Requirement: The Python wrappers check policy input
The action kit SHALL check `policy` and `slot` and `signed` before it sends `policy_enact` or `policy_sign`, and SHALL raise an error when the game refuses a command.

#### Scenario: Bad wrapper input
- **WHEN** a scenario calls `policy_enact` with a policy id of 0 or a negative slot, or `policy_sign` with `signed` that is not a boolean
- **THEN** the action kit raises an error and sends no command
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

#### Scenario: A refused command raises
- **WHEN** the game refuses a policy command
- **THEN** the action kit raises `CommandRefused`
- Checked by `harness/tests/test_fakegame_harnesspolicies.py`.

### Requirement: A policy widget can be shown for a menu spike
The harness SHALL put one game policy widget on the screen on `menu_probe_show` with `policy` and optional `x` and `y`. `menu_probe_read` SHALL poll the state of its button. `menu_probe_hide` SHALL remove it. The harness SHALL refuse a second widget while one is shown, and a policy id outside 1 to 40.

#### Scenario: A second widget
- **WHEN** a probe widget is on the screen and a client sends `menu_probe_show`
- **THEN** the reply is not ok and says to call `menu_probe_hide` first
- Not checked yet.
