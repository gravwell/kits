This kit is designed to provide an out-of-the-box experience for working with Thinkst Canary logs.

It provides the following utilities:
- Actionables
- Alerts
- Autoextractors
- Dashboards
- Flows
- Macros
- Playbooks
- Queries
- Resources
- Scheduled Searches
- Templates

Refer to the [Integration Guide](https://docs.gravwell.io/integrations/network/thinkst.html) for setup instructions, and the Kit Overview playbook for more detail on components.

The Thinkst Canary kit is licensed under the BSD 2-Clause license and the contents are available on [Github](https://github.com/gravwell/kits/tree/main/thinkstcanary).

## Dependencies
- Gravwell Network Enrichment Kit (version 19 or later)
	- The MaxMind database it ships is required for the Location queries, scheduled searches, and alerts.

## Changelog
**v2: Refactoring**
- Fixes: macro layer risk score no longer silently skips its unacknowledged-incident and event-count bonuses (a has() check was testing string literals, not field values); the alert priority EV is now actually populated
- Fixes: thinkst-incident autoextractor now extracts the events_count/events_list fields, fixing queries that were silently dropping them
- Fixes: regex named-capture groups corrected from invalid to valid Go-syntax on affected alert queries
- Fixes: template variable mislabeling corrected (the "Acknowledged" field was actually named result)
- Fixes: a stray space in an alert-metadata call was mislabeling the Ignorelist IP/Port Removed alert's category
- Fixes: dashboard tile aliases and one dashboard's own name corrected to match kit naming convention
- Fixes: removed 3 duplicate resources ("Multiple SMS Notification(s) List Actions" alert/scheduled search/query, and a duplicate "Incident" flow)
- Fixes: playbook Markdown backtick-delimited config snippets and an inline mention no longer render as broken query-launch buttons
- Fixes: resolved kitcheck findings for macro leading-pipe errors, unlinked kit images, unlabeled actionable pivots, duplicate actionable menu labels, and a missing integration-guide mention in README
- Changes: consolidated risk-scoring/incident-metadata logic (previously copy-pasted into every query) into shared $CANARY\_RISK\_SCORE/$CANARY\_INCIDENT\_META macro calls
- Changes: template variables renamed from positional numbering to named variables
- Changes: alert Labels and UID fields normalized for consistency; legacy ThingUUID field removed
- Changes: kit images (banner, cover) converted from duplicate files to symlinks per Standards §5.2/§16
- Changes: Integration Guide moved to a published doc (docs.gravwell.io); README and Kit Overview repointed at it, in-kit playbook removed
- Changes: Kit Overview's Image Credits section removed
- Adds: 2 actionable pivots (Investigate IP Address, Correlate Flock Activity)
- Adds: 1 new search (Audit - Count [numbercard])

 **v1: Initial Release**
