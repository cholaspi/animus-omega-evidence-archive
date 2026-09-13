# Persistent multi-agent closure: development harness 1

**Toy development harness for a proposed reserved evaluation. No reserved seeds were run. Not evidence.**

This directory contains the larger deterministic development harness used to exercise six-agent state, ledger, replay, model-adapter replacement, fault fixtures, and closure-validation code paths.

It remains separate from [`../lab-slice/`](../lab-slice/):

- `lab-slice` is the small grader demo intended for quick review and porting.
- `pmc-dev-1` is the larger toy development harness used to expose protocol and implementation problems before any reserved work.

The architect review remains no-go for treating this harness as a valid comparative benchmark. Its passing development episodes establish engineering behavior only, not a closure advantage, production-model resilience, or confirmatory evidence.

Run from this directory:

```bash
cd experiments/pmc-dev-1
python3 run_persistent_closure_benchmark.py --output-dir /tmp/pmc-dev-1
python3 -m unittest discover -s tests -v
```

Active work belongs in [Issue #1](https://github.com/cholaspi/animus-omega-evidence-archive/issues/1). The development protocol remains in [`docs/PERSISTENT_MULTI_AGENT_CLOSURE_BENCHMARK.md`](../../docs/PERSISTENT_MULTI_AGENT_CLOSURE_BENCHMARK.md).