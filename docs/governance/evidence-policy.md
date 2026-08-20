# Evidence policy

## States

`PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY`, and `HUMAN_ADMIT_REQUIRED` retain distinct meanings.

## Lanes

- `SOURCE`: vendor documentation, talk, article, model card, repository.
- `STATIC`: schema, compilation, unit tests, deterministic fixtures.
- `LOCAL`: emulator/simulator or local runtime on an exact revision.
- `LIVE_DEVICE`: physical hardware and actual selected backend.
- `PRIVATE`: private dataset, terms acceptance, signed-in source, or confidential lineage.
- `HUMAN`: merge, release, legal acceptance, store publication, destructive action.

A receipt satisfies only its own lane and exact subject.

## Benchmark contract

Every benchmark binds model ID/version/digest, runtime version, device, OS, backend actually used, quantization, input/output token counts, prompt/task set, sampler settings, temperature/thermal state, memory, power policy, and evidence state. Numbers copied from a talk remain `SOURCE_REPORTED` until reproduced.
