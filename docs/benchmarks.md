# Benchmark methodology

RepoLens favors reproducible measurements over headline numbers. No performance
claim should be published without the repository revision, hardware/OS, Python
version, command, fixture or corpus description, warm-up policy, and raw results.

## Run a local benchmark

```bash
python scripts/benchmark.py ./path/to/repository --runs 10 --warmup 2
```

The script measures the in-process scan and complete analysis-pipeline durations and
writes one JSON record to standard output. The warm-up runs are excluded from the
reported summary. Redirect output to a file when comparing revisions:

```bash
python scripts/benchmark.py ./path/to/repository --runs 10 --warmup 2 > results.json
```

## Reporting rules

- Use the same target commit and clean working tree for compared runs.
- Repeat enough measured runs to report a median and range, not one timing.
- Do not compare warm cache and cold cache results without labeling them.
- Mark runs with zero successful measurements as invalid; never replace missing data
  with an estimate.
- Report repository size and file counts alongside timings.

The benchmark harness is a development aid, not a CI gate. It intentionally does
not contact the network, execute the target project, or collect telemetry.
