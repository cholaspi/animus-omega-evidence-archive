"""Safe development-only output runner."""

from __future__ import annotations

import argparse
import hashlib
import platform
import sys
import time
from pathlib import Path
try:
    import resource
except ImportError:  # pragma: no cover - Windows development fallback
    resource = None

from .benchmark import run_benchmark
from .serialization import canonical_bytes, sha256_bytes

DEFAULT_OUTPUT = Path("/tmp/persistent_closure_benchmark")

def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="development-only closure benchmark")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args(argv)
    output = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    result = run_benchmark()
    results_path = output / "results.json"
    marker_path = output / "DEV_NON_CONFIRMATORY"
    results_path.write_bytes(canonical_bytes(result))
    marker_path.write_text(
        "Development output only; no confirmatory or reserved-seed claim.\n",
        encoding="utf-8",
    )
    checksums = [
        f"{sha256_bytes(marker_path.read_bytes())}  {marker_path.name}",
        f"{sha256_bytes(results_path.read_bytes())}  {results_path.name}",
    ]
    (output / "SHA256SUMS").write_text(
        "\n".join(sorted(checksums)) + "\n",
        encoding="utf-8",
    )
    runtime = {
        "status": "development_non_confirmatory",
        "wall_time_ns": time.perf_counter_ns() - wall_start,
        "cpu_time_ns": time.process_time_ns() - cpu_start,
        "peak_rss_bytes": (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                           if resource is not None else None),
        "results_file_bytes": results_path.stat().st_size,
        "model_calls": sum(
            a["model_schedule"]["model_calls"]
            for e in result["episodes"] for a in e["arms"]),
        "model_tokens": sum(
            a["model_schedule"]["tokens"]
            for e in result["episodes"] for a in e["arms"]),
        "replay_steps": sum(
            a["metrics"]["replay_steps"]
            for e in result["episodes"] for a in e["arms"]),
        "validation_steps": sum(
            a["metrics"]["validation_steps"]
            for e in result["episodes"] for a in e["arms"]),
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "note": "Nondeterministic descriptive runtime measurements; excluded from canonical scientific result.",
    }
    runtime_path = output / "runtime.json"
    runtime_path.write_bytes(canonical_bytes(runtime))
    source_files = sorted(Path("persistent_closure_benchmark").glob("*.py"))
    source_manifest = {
        str(path): sha256_bytes(path.read_bytes()) for path in source_files
    }
    protocol_path = Path("docs/PERSISTENT_MULTI_AGENT_CLOSURE_BENCHMARK.md")
    protocol_manifest = {
        str(protocol_path): sha256_bytes(protocol_path.read_bytes())
    } if protocol_path.exists() else {}
    manifest = {
        "status": "development_non_confirmatory",
        "reserved_seeds_not_run": result["reserved_seeds_not_run"],
        "protocol_digest": result["episodes"][0]["public_inputs"]["protocol_digest"],
        "source_manifest": source_manifest,
        "protocol_manifest": protocol_manifest,
        "result_checksum": result["result_checksum"],
        "files": {
            path.name: sha256_bytes(path.read_bytes())
            for path in (results_path, runtime_path, marker_path)
        },
        "replay_command": result["episodes"][0]["replay_command"],
        "deviations": [],
        "clean_room_independent_implementation": "pending Task 79",
        "real_provider_replacement": "pending Task 78",
    }
    (output / "manifest.json").write_bytes(canonical_bytes(manifest))
    return output

if __name__ == "__main__":
    main()