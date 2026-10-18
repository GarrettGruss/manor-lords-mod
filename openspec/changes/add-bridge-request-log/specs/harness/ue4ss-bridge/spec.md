## ADDED Requirements
<!-- Issue: #270 -->

### Requirement: Each request is logged live
The bridge Lua mod SHALL write one line to `HarnessLog` for each request it handles. The line SHALL hold the request id, the verb, the target and the duration in milliseconds. A failed request SHALL log its error text. The log line SHALL NOT hold property values or Lua source.

#### Scenario: A read request
- **WHEN** a client sends a read request and the mod answers it
- **THEN** `mod.log` of the run holds one line with the id, the verb `get`, the target and a duration
- **AND** the line is flushed at once
- Not checked yet (planned: `harness/tests/test_fakegame_uebridge.py`).

#### Scenario: A failed request
- **WHEN** a request names an object that does not exist
- **THEN** the log line says the request failed and holds the error text
- Not checked yet (planned: `harness/tests/test_fakegame_uebridge.py`).

#### Scenario: An eval request
- **WHEN** a client sends a raw Lua eval request
- **THEN** the log line holds the verb and the id but not the Lua source
- Not checked yet (planned: `harness/tests/test_fakegame_uebridge.py`).
