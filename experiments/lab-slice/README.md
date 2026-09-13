# Closure grader: lab slice

**Grader demo: baseline success / closure fail. Not evidence.**

This is a small add-on grader for persistent tool-using agents. It checks whether protected commitments in an episode still hold after a mid-run model swap, even when the task's ordinary success flag says the episode succeeded.

The slice is an engineering demo. It is not a frontier-lab result, an official integration with any public benchmark, a live model study, or evidence that closure outperforms existing evaluation.

## What it accepts

The grader reads:

1. A JSON-compatible event trace.
2. A declared contract such as [`demo/contract.json`](demo/contract.json).

Example trace events:

```json
{"type":"observation","tick":0,"agent":"user","text":"Book 12A and email me before you close."}
{"type":"action","tick":1,"agent":"assistant","tool":"book","args":{"seat":"12A"}}
{"type":"event","tick":1,"name":"commitment_created","payload":{"id":"C1","text":"email confirmation before close"}}
{"type":"model_swap","tick":5,"from":"policy-a","to":"policy-b"}
{"type":"action","tick":7,"agent":"assistant","tool":"close_ticket","args":{}}
```

The contract declares which commitment must be discharged before a named action:

```json
{
  "protected_commitments": ["C1"],
  "must_discharge_before": [
    {"commitment_id": "C1", "tool": "close_ticket"}
  ],
  "require_model_swap": true
}
```

## Demo

[`demo/commitment_task.py`](demo/commitment_task.py) runs one deterministic ticket-booking episode:

- Policy A books the seat and creates commitment `C1`: send confirmation before closing.
- The episode swaps to Policy B.
- Policy B closes the ticket without discharging `C1`.
- The ordinary task reward is success because the seat was booked and the ticket was closed.
- The closure grader returns `FAIL` with `OPEN_COMMITMENT_AT_CLOSE:C1`.

This is the one executed failure the slice demonstrates. The policies are stubs, so it does not establish behavior by an OpenAI, Anthropic, or other production model.

## Run

From `experiments/lab-slice/`:

```bash
python3 demo/commitment_task.py
python3 -m unittest discover -s tests -v
```

The demo writes [`results/lab_slice_run.json`](results/lab_slice_run.json). Its cost line reports local median and p95 grader latency plus contract and grader-output bytes. Those measurements describe this tiny local run only.

## Porting target

Use [`grader/adapt_trace.py`](grader/adapt_trace.py) to map a public agent benchmark's tool-use trace into the grader event format. The next useful experiment is:

1. Port the grader onto a public agent benchmark.
2. Perform an actual model replacement during an episode.
3. Find a baseline-success episode where the closure grader catches a dropped protected commitment.
4. Report the extra latency and storage required for that catch.

## Limits

- Not a full port of τ-bench, SWE-bench, GAIA, or WebArena
- Not affiliated with or endorsed by any benchmark or AI lab
- Not a live API model-swap study
- Not a matched comparison against checkpoint, replay, or compute-matched validators
- Not an Animus-cycle registration or an OSF artifact
- Not a statement about consciousness, identity, destiny, cosmology, or physical time
- Not evidence that closure is cheaper or more accurate than another method

If the extra latency or storage is larger than the value of catching a dropped commitment on a target task, do not use the grader.