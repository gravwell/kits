# LLM Observability

LLM traffic is the one thing in most environments nobody is logging. The prompts your staff paste
into a model, the tools that model invokes on their behalf, and the tokens you get billed for all
move through an HTTPS request that never touches your SIEM.

This kit turns that traffic into data you can chart and hunt through. It is built on three Gravwell
5.10 features that chain together:

- the **LLM ingester**, an OpenAI-compatible proxy that records prompts, replies, reasoning, tool
  calls, tool results, and token usage;
- the **vector preprocessor**, which attaches an embedding to each entry at ingest;
- the **semantic** search module, which scores entries by meaning against a phrase you write.

The point of the third one is that keyword rules do badly against prose. Someone trying to talk a
model out of its instructions might write *ignore your previous instructions*, *disregard everything
above*, or a paragraph of roleplay that uses none of those words. A regex catches the phrasings you
thought of; a semantic hunt catches the intent.

The LLM Observability kit is licensed under the BSD 2-Clause license and the contents are available
on [Github](https://github.com/gravwell/kits/tree/main/llm_observability).


## Requirements

- Gravwell 5.10 or later.
- The [Gravwell LLM ingester](https://docs.gravwell.io/ingesters/llm.html) deployed as a proxy in
  front of your model provider, with `Log-Tool-Calls=true` and `Log-Usage=true` on the listener.
- **For the semantic hunts only:** the
  [vector preprocessor](https://docs.gravwell.io/ingesters/preprocessors/vector.html) attached to an
  LLM listener, plus `Embedding-URL`, `Embedding-Model`, and `Embedding-Token` in the `[AI]` section
  of the webserver's `gravwell.conf`. The two embedding models must be the same one.
- **For the `llm-triage` agent only:** an LLM configured on the deployment.

Everything except the *LLM Semantic Risk Hunting* dashboard and the *Semantic Hunt* template works
on plain proxy data, so it is reasonable to install the kit before you decide whether to pay for
embeddings.

Set the `LLM_TAG` configuration macro at install time to whatever `Tag-Name` your LLM listener writes
to. `LLM_SEMANTIC_THRESHOLD` tunes every semantic hunt at once; it ships at 70.


## Contents

### Dashboards

- **LLM Traffic Overview** — reply volume by model, which event types are actually being logged,
  token spend, upstream errors, per-listener traffic, new sessions. Start here.
- **LLM Cost and Token Usage** — token totals and the prompt-versus-completion split per model, and
  the conversations costing the most. Needs `Log-Usage=true`.
- **LLM Performance and Reliability** — latency per model over time, the slowest individual requests,
  and every non-2xx response from the provider.
- **LLM Tool Use** — which tools the models call, how often, and the argument JSON for recent
  invocations. Needs `Log-Tool-Calls=true`.
- **LLM Semantic Risk Hunting** — seven prebuilt meaning-based hunts plus a free-text one. Needs
  embeddings.

### Templates

- **Semantic Hunt** — describe a behaviour in plain language; get scored results back. Takes the
  phrase, the `event_type` to score, a model filter, and a threshold.
- **Conversation Reconstruction** — give it a `session_id` and read the whole exchange in order.

### Semantic hunts

Six against user prompts — prompt injection and jailbreak attempts, credentials and secrets pasted
into a model, sensitive data and PII disclosure, data exfiltration intent, destructive operations
requested, and security control evasion — plus one against replies, **Model Refusals**, which is
underrated: a cluster of refusals inside one session is a strong signal that someone is probing.

### Macros

`$LLM_TAG` and `$LLM_SEMANTIC_THRESHOLD` are configuration macros.

The other six exist because of how the ingester attaches its fields. Everything the LLM proxy
records — `event_type`, `session_id`, `model`, `total_tokens`, `embeddings`, all of it — arrives as an
**intrinsic** enumerated value: present on the entry, but invisible to the query engine until you
declare it with the [`intrinsic`](https://docs.gravwell.io/search/intrinsic/intrinsic.html) extraction
module. Referencing an undeclared one is a hard error, not an empty result.

These macros wrap that module with the `event_type` filter already inline:

```
$LLM_USER_PROMPTS      ->  intrinsic event_type == "request.user_message"
$LLM_SYSTEM_PROMPTS    ->  intrinsic event_type == "request.system_message"
$LLM_ASSISTANT_REPLIES ->  intrinsic event_type == "response.assistant_message"
$LLM_TOOL_CALLS        ->  intrinsic event_type == "response.tool_call"
$LLM_TOOL_RESULTS      ->  intrinsic event_type == "request.tool_result"
$LLM_USAGE             ->  intrinsic event_type == "response.usage"
```

They go in the extraction position — straight after the tag block, no pipe — and you append whichever
further fields the query needs onto the same module:

```
tag=$LLM_TAG $LLM_USAGE model total_tokens
| stats sum(total_tokens) as Tokens by model
| chart Tokens by model
```

Two things worth knowing before writing your own: `embeddings` has to be declared before `semantic`
can read it (omit it and the hunt looks exactly like "we have no embeddings"), and the `text` and
`raw` renderers declare every intrinsic value for you, so a query can work under `raw` and fail the
moment you switch it to `table`.

Inline filters on that module are equality only — there is no `<`, `>`, `<=`, or `>=`. For a numeric
comparison, declare the field and test it after a pipe with a cast, which is what the upstream-error
queries do:

```
tag=$LLM_TAG intrinsic upstream_status
| eval int(upstream_status) >= 400
| stats count as Errors by upstream_status
| chart Errors by upstream_status
```

### Playbooks

- **Kit Overview** — the three-feature chain and what works without embeddings.
- **Deploying the LLM Proxy** — install, listener config, log modes, the two authorization
  credentials, TLS, sessions, pointing clients at it, verifying data arrives.
- **Enabling Semantic Search** — the vector preprocessor, the `[AI]` section, why the two models must
  match, and the throughput and storage costs you are signing up for.
- **Hunting Prompts by Meaning** — thresholds, when to use `-p`, how to write a phrase that works,
  and why `semantic` must always come last in the pipeline.

### Resources

- **Example Gravwell LLM Ingester Conf** — a complete commented config with the vector preprocessor
  already wired to the listener. Replace the `CHANGE_ME` placeholders.
- **llm-triage-gravwell.agent** — a read-only AI agent that takes a flagged prompt and investigates
  it: replays the session and the tool calls it drove, baselines whether the behaviour is normal for
  that listener, hunts semantically for other sessions with the same intent, rules out retry storms
  and logging gaps, then writes a verdict with evidence and follow-up queries.


## Performance and privacy

Two things worth knowing before you turn this on for a whole team.

**The semantic module is expensive.** It runs on the webserver, so every entry it evaluates has its
vector — roughly 10-20KB for a 1024-dimensional model — shipped from the indexers first. Every hunt
in this kit narrows by tag, timeframe, and `event_type` *before* the `semantic` module for that
reason. Keep that ordering in anything you write.

**You are recording what people typed into a model.** That is sensitive by construction: prompts
routinely contain customer data, source code, and credentials. Decide deliberately which `Log-Mode`
you run, who gets read access to the tag through CBAC, and how long the well retains it. `Log-Mode=user`
exists precisely so you can capture what users asked without archiving every system prompt and
document your application stuffs into the context window.

This kit contains no automations, and nothing in it sends data to an external system.
