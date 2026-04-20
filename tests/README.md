# Layer 5: Testing Infrastructure

Every layer of Prosper0 is independently testable. No real employer data is ever used in tests.

## Structure

```
tests/
├── sample_data/        ← synthetic vault generator
├── model_comparison/   ← prompt battery + diff harness
├── bridge/             ← bridge integration tests
├── boundary/           ← data isolation assertion tests
└── tool_config/        ← tool permission enforcement tests
```

## Sample Data

`sample_data/` contains the generator for synthetic Prosper0 vault content: realistic tasks, projects, decisions, and daily notes at configurable volume and scenario type. Run the generator before any test that touches vault content.

## Model Comparison

`model_comparison/` runs a standard prompt battery against registered model versions and diffs outputs. Adding a model: one config line. Re-running: one command.

## Data Boundary Tests

`boundary/` asserts that no personal exobrain content appears in Prosper0 responses and vice versa. These tests are the structural proof that vault isolation and bridge controls work as designed.

## Tool Config Enforcement Tests

`tool_config/` verifies that the AI cannot invoke disabled tools — including under adversarial prompting. These tests treat the enforcement layer as a security boundary.
