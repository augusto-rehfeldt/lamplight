"""Compare explicit HyperCharm models using Lamplight's real qualification requests.

python bench_lamplight.py --models llama-3.3-70b-instruct qwen3.8-flash deepseek-v4-flash
Uses AW_API_KEY and AW_BASE_URL from the environment or this project's .env.
Only synthetic tasks are sent; game saves and qualification are untouched.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import time

import game_native as native
import lamplight_ai as ai


def benchmark(models, url, key, output, repeat=1, seed=42):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    tasks = [ai.cases(seed + i) for i in range(repeat)]
    report = dict(created=dt.datetime.now(dt.timezone.utc).isoformat(), url=url,
                  version=ai.VERSION, seed=seed, repeat=repeat,
                  max_tokens=ai.MAX_TOKENS, timeout=ai.TIMEOUT, results=[])
    (output / "tasks.json").write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="lamplight-benchmark-") as temporary:
        library = native.Library(Path(temporary))
        for model in dict.fromkeys(models):
            library.request(dict(op="ai_config", url=url, model=model, key=key, enabled=True))
            config = library.state["settings"]["ai"]
            for index, batch in enumerate(tasks, 1):
                print(f"{model} [{index}/{repeat}]: starting", flush=True)

                def send(system, prompt):
                    request = dict(model=model, trial=index, task=json.loads(prompt)["task"])
                    started = time.monotonic()
                    try:
                        answer = library.send_ai(config, key, system, prompt, ai.MAX_TOKENS, ai.TIMEOUT)
                        request["answer"] = answer
                        return answer
                    except native.legacy.requests.RequestException as error:
                        # Exception bodies can contain provider diagnostics; keep credentials out of reports.
                        request["error"] = type(error).__name__
                        raise ValueError("Provider connection failed: " + type(error).__name__) from None
                    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                        request["error"] = "Incompatible chat response"
                        raise ValueError(request["error"]) from None
                    except ValueError as error:
                        request["error"] = str(error)
                        raise
                    finally:
                        request["seconds"] = round(time.monotonic() - started, 2)
                        with (output / "requests.jsonl").open("a", encoding="utf-8") as log:
                            log.write(json.dumps(request) + "\n")
                        print(f"  {request['task']}: {request['seconds']:.2f}s" +
                              (" - " + request["error"] if "error" in request else ""), flush=True)

                started = time.monotonic()
                try:
                    result = ai.run(send, tasks=batch)
                    result["status"] = "passed" if result["passed"] else "not_qualified"
                except ValueError as error:
                    result = dict(status="request_error", error=str(error),
                                  seconds=round(time.monotonic() - started, 2))
                result.update(model=model, trial=index)
                report["results"].append(result)
                (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                print(f"  {result['status']} | score {result.get('score', 'n/a')} | {result['seconds']:.2f}s", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", required=True, help="Exact HyperCharm model IDs; no fallback")
    parser.add_argument("--repeat", type=int, default=1, help="Trials per model, each with three requests")
    parser.add_argument("--seed", type=int, default=42, help="Reproducible synthetic tasks shared by all models")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output" /
                        dt.datetime.now().strftime("lamplight-bench-%Y%m%d-%H%M%S-%f"))
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    key = os.environ.get("AW_API_KEY", "")
    if not key:
        parser.error("Set AW_API_KEY in the environment or project .env")
    report = benchmark(args.models, os.environ.get("AW_BASE_URL", "https://hyper.charm.land/v1"),
                       key, args.output, args.repeat, args.seed)
    print(f"Report: {args.output / 'report.json'}")
    return 0 if all(r["status"] == "passed" for r in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
