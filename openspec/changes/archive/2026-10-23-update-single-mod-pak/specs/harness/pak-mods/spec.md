## ADDED Requirements
<!-- Issue: #471 -->

### Requirement: Cooked widgets are mod pak assets
A cooked Widget Blueprint (`.uasset` and `.uexp`) SHALL be a file under `data/<feature>/assets/`, so `buildmod` puts it in the same pak as the table rows. One widget file SHALL have one owner feature.

#### Scenario: A widget in the mod pak
- **WHEN** `buildmod` runs for a mod with a widget asset in a feature
- **THEN** the pak holds the widget and the table rows
- Checked by `harness/tests/test_modpak.py` and `harness/tests/test_invasionmod_pak.py`.
