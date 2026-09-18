# Gravwell Windows Sysmon Kit

This kit provides dashboards, searches, templates, and investigative resources for
Microsoft Windows Sysmon data — event volume overviews, process/DNS/registry
investigation dashboards, and a large query library covering process creation,
driver loads, remote thread injection, DNS, file, and registry events.

See the [Gravwell Sysmon Integration Guide](https://docs.gravwell.io/integrations/host/sysmon.html)
for ingester setup.

This kit provides the following utilities:

- Queries
- Dashboards
- Macros
- Resources
- Templates
- Actionables
- Playbooks

Refer to the Kit Overview playbook for more detail on these components.

## Dependencies

* io.gravwell.windows.resource (MinVersion 1)
* io.gravwell.networkenrichment (MinVersion 6)

The Windows Resource kit supplies windows_access_flags and windows_error_codes; the Network Enrichment kit supplies dns_types, network_services and the asn_db GeoIP database.

## Changelog

**v8: Audit remediation**
- Corrected the ProcessGuid File Delete template to Event ID 23, the Sysmon Errors search (Event ID 255 emits no RuleName), and the registry Environment path literal.
- Fixed time-windowed aggregation on the Integrity Level deviation chart and the network_services composite join.
- Widened aggregations that discarded fields their tables named, and scoped every kv to the Hashes field.
- Added Sysmon 13/14 event IDs (26-29) to the sysmon_event_ids resource.
- Added a Sysmon Computer actionable feeding the Investigate Computer dashboard, and rewired four mis-pointed dashboard tiles.
- Replaced the banner and cover art with the standard Gravwell kit branding, and added a matching icon.
- Renamed the "Sysmon Gravwell Kit" playbook to "Sysmon - Kit Overview" to match kit naming conventions, and added a "Sysmon - Readme" playbook synced from this README.
- Fixed playbook rendering issues: a missing space after the Overview heading, and four spots where a raw-HTML block (a config example, two XML event samples, the EventIDs table) ran directly into the following section heading with no visible gap.
- Streamlined this README to the current kit documentation convention and added the [Integration Guide](https://docs.gravwell.io/integrations/host/sysmon.html) reference.
- Renamed every dashboard, search, and actionable to the "Sysmon - X" convention, replacing the inconsistent "Sysmon: X" (searchlibrary) and bare "Sysmon X" (dashboard/actionable) forms; synced 28 dashboard tile aliases and the Kit Overview playbook's stale prose references to match. Updated two actionable menu labels ("DNS" -> "Sysmon DNS", "ProcessGuid" -> "Sysmon Process GUID") to indicate which kit they belong to.
- Renamed every template to the same "Sysmon - X" convention (one, "Event Counts by ProcessGuid", had no kit prefix at all); synced 22 dashboard tile aliases to match.
- Renamed 10 templates' variable from "_GUID_"/"_HASH_" to the standard "%%GUID%%"/"%%HASH%%" convention every other real kit uses; synced each template's own query and the 3 pivot actions that referenced them.

**v6: Initial catalogued release**
