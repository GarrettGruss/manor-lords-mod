## MODIFIED Requirements
<!-- Issue: #414 -->

### Requirement: Reference images from Gemini
The tool `harness/tools/genimage.py` SHALL generate 1 to 4 images for each call. It SHALL read the key from `GEMINI_API_KEY` (environment, else Windows user scope), SHALL fail with a clear message when the key is missing, and SHALL NOT print the key. It SHALL take 0 to 3 reference images with `--ref` and send them with the prompt in the same request. It SHALL append each call to `runs/genimage/log.jsonl`. With `--list-models` it SHALL list the image models the key can use.

#### Scenario: Count out of range
- **WHEN** `--count` is 0 or above 4
- **THEN** the tool stops with a message that gives the range
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: A call is logged
- **WHEN** images are generated
- **THEN** one line is added to `runs/genimage/log.jsonl` with the model, the prompt, the output files and their sizes, and the reference files with their SHA-256 hashes
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: References are sent with the prompt
- **WHEN** `--ref` is given one to three times with a Gemini model
- **THEN** the request holds one image part for each reference, in the given order, followed by the text prompt
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: Too many references
- **WHEN** `--ref` is given four or more times
- **THEN** the tool stops with a message that gives the range, and makes no API call
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: A bad reference file
- **WHEN** a reference file is missing, is not PNG, JPEG or WebP, or is larger than 7 MB
- **THEN** the tool stops with a message that names the file and the reason, and makes no API call
- Checked by `harness/tests/test_genimage.py`.

#### Scenario: References with an Imagen model
- **WHEN** `--ref` is given with a model whose name starts with `imagen`
- **THEN** the tool stops with a message that only Gemini models take references, and makes no API call
- Checked by `harness/tests/test_genimage.py`.
