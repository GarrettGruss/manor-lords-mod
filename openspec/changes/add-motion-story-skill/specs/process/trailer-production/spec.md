## ADDED Requirements
<!-- Issue: #407 -->

### Requirement: Creative approvals come before the full media set
An agent SHALL get the owner's explicit approval of the visual style (style preamble and a test set of at most 3 stills) and of the shot plan (chapters, copy, camera moves, connectors) before it generates the full still set or writes the final video manifest. Silence or an earlier general instruction SHALL NOT count as approval.

#### Scenario: No style approval yet
- **WHEN** the test stills are ready and the owner has not answered
- **THEN** the agent does not generate more stills
- Checked by review.

### Requirement: Each paid video batch needs its own cost approval
Before the first paid request of a batch, the agent SHALL show the owner the number of clips, their durations, the model and the estimated cost, and SHALL wait for explicit approval. A creative approval SHALL NOT count as cost approval. The pipeline SHALL refuse to send more requests than the clip cap of the batch.

#### Scenario: A batch above the cap
- **WHEN** a batch has 12 clips and the cap is 8
- **THEN** the pipeline sends no request and names the cap
- Checked by `.claude/skills/sn-motion-html/tests/` (planned).

#### Scenario: A billing error
- **WHEN** the provider answers with an authentication, billing or model-activation error
- **THEN** the pipeline stops without a retry and reports the error code
- Checked by `.claude/skills/sn-motion-html/tests/` (planned).

### Requirement: Every paid request is logged without secrets
The pipeline SHALL append one line per paid request to the spend log of the project, with the clip id, model, duration, task id and final status. The log SHALL NOT hold the key, the Authorization header or image data URLs.

#### Scenario: The log after a batch
- **WHEN** a batch of 3 clips ends
- **THEN** the spend log has 3 new lines and none of them holds the key
- Checked by `.claude/skills/sn-motion-html/tests/` (planned).

### Requirement: Generated media stays out of git
Generated clips, frames, stills under review and exported videos SHALL NOT be committed. Only story data, prompts, manifests, the page code, and approved posters of at most about 1 MB in total MAY be committed. Picture evidence follows the normal evidence rules.

#### Scenario: A clip in the working tree
- **WHEN** a story project has rendered clips in its media folder
- **THEN** `git status` does not list them
- Checked by review.
