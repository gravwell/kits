# AI Agent Preview

This kit packages a preview set of six Gravwell AI agents.

Unlike most kits, it contains no searches, dashboards, templates, or automations.
Each agent is a JSON agent definition carried in a resource whose name ends in
`-gravwell.agent`; Gravwell picks those resources up and offers them in the AI
agent list alongside the built-in assistant. Installing the kit is all that is
needed to make the agents selectable.

Start with the **AI Agent Preview - Kit Overview** playbook, which covers what
each agent is for, how to choose between them, and how to drive the automated
ones from a flow.


## Contents

Conversational agents -- you talk to these:

- **case-agent** -- investigation partner for Query Studio. Carries the full
  Gravwell query language reference, so it writes, validates, and runs queries
  with you, reads the results, tracks the case across turns, and proposes the
  next pivot. Use it for threat hunting and iterating on queries.
- **gravwell-admin** -- administration and configuration assistant. Covers every
  ingester, CBAC, wells and storage, replication, preprocessors, resources, and
  tokens and secrets. It does not write or run queries.
- **mechanic** -- troubleshooter for the deployment itself. Triages errors in the
  `gravwell` tag, diagnoses dead ingesters, stalled scheduled searches, and
  unhealthy indexers, and runs any single audit check on demand.

Automated agents -- these run unattended and produce a Markdown report:

- **alert-triage** -- first-pass triage of a firing alert. Reads the alert
  definition and its firing history, pulls ground truth about the entities out of
  the raw data, baselines the behaviour, checks runbooks and platform health, then
  writes a verdict with evidence and validated queries for the responder. The
  alert payload is its input, so attach it to an alert.
- **gravwell-audit** -- health and hygiene audit of the whole deployment. Five
  auditors run in parallel over automation, alerts, the content library,
  infrastructure, and data flow, then merge into one prioritised report.
- **daily-summary** -- nightly activity digest covering ingest volume against a
  weekly baseline, notable activity, what alerts and automation did, and platform
  health. Writes a short Markdown message for the operator; intended for a
  nightly schedule.


## Requirements

An LLM must be configured on the deployment before any of these agents can run.

Every agent is read-only against the deployment except `case-agent`, which can
save a query when you explicitly ask it to. None of them send data to an external
system beyond the configured LLM.
