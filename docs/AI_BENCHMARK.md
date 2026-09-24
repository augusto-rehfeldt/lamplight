# HyperCharm gameplay qualification — 2026-09-09

The live benchmark used the existing project `AW_API_KEY` at
`https://hyper.charm.land/v1`. Credentials were not copied into reports.
The provider's authenticated model catalogue confirmed all six requested IDs.

## Final benchmark, version 2

Two trials per model, seeds 42 and 43. Each trial contains source grounding,
period/evidence and gameplay reasoning tasks. Models received identical tasks.
Requests use the same HTTP transport and scorer as the game, with 700 output
tokens, a 25-second read timeout and no retries or provider fallback.

| Requested model | Scores | Qualified trials | Total seconds per trial |
| --- | --- | --- | --- |
| `deepseek-v4-flash` | 100, 100 | 2/2 | 18.74, 19.38 |
| `qwen3.8-max` | 100, 100 | 2/2 | 42.79, 52.03 |
| `gemma-4-26b-a4b-it` | 92, 75 | 0/2 | 7.95, 7.14 |

DeepSeek Flash was the faster qualifying model in this sample. Gemma's first
trial failed the action sequence; its second also failed both resource balances.
A high average cannot override a critical gameplay error.

Reproduce from the project root:

```powershell
rtk python bench_lamplight.py --models gemma-4-26b-a4b-it deepseek-v4-flash qwen3.8-max --repeat 2
```

The measured [report](../output/lamplight-bench-hyper-v2-20260909/report.json),
[request/reply log](../output/lamplight-bench-hyper-v2-20260909/requests.jsonl)
and [tasks](../output/lamplight-bench-hyper-v2-20260909/tasks.json) are local
generated artifacts under the ignored output directory.

## Exploratory version 1

The original prompt said to return a source marker without explicitly mentioning
its brackets. Several models omitted them. Version 2 clarifies the prompt;
the scorer and pass thresholds are unchanged. These earlier scores should not be
compared directly with version 2:

| Requested model | Outcome | Total seconds |
| --- | --- | --- |
| `llama-3.3-70b-instruct` | 42; failed gameplay, marker and prose checks | 5.29 |
| `qwen3.8-flash` | Read timeout on the first request; no score | 25.93 |
| `deepseek-v4-flash` | 83; failed exact source-marker checks | 15.79 |
| `gemma-4-26b-a4b-it` | 83; failed exact source-marker checks | 10.57 |
| `glm-5.3-flash` | Exhausted output token limit; no score | 14.56 |
| `qwen3.8-max` | 92; failed source ID check | 48.66 |

Raw exploratory reports are in `output/lamplight-bench-hyper-20260909/` and
`output/lamplight-bench-hyper-more-20260909/`. Failed transport or truncated replies
do not establish model weakness. The runner stops that trial and continues with
the next one, preserving already completed request logs.

This small synthetic check tests qualification under the game's limits, not
general intelligence, literary quality or historical accuracy. A seeded task is
repeatable; provider replies and latency need not be. The runner does not grant
qualification to a running game: use **Connect & benchmark** there.

Validation: all 31 Python gameplay/AI tests passed, including identical-model
inputs, error continuation, key privacy, save isolation and truncated-response
rejection. Godot's headless integration check also passed.
