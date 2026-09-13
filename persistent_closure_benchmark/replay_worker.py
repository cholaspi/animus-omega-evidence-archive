"""Fresh-process worker for public-input replay."""

from __future__ import annotations

import json
import sys

from .benchmark import replay_public_inputs
from .serialization import serialize_result

def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        raise SystemExit("usage: python -m persistent_closure_benchmark.replay_worker INPUT OUTPUT")
    with open(argv[0], "rb") as source:
        inputs = json.load(source)
    result = replay_public_inputs(inputs)
    with open(argv[1], "wb") as target:
        target.write(serialize_result(result))

if __name__ == "__main__":
    main()