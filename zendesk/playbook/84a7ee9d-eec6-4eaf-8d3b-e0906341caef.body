This kit is designed to provide an out-of-the-box experience for working with Zendesk audit logs.

The Zendesk audit log records changes made to your Zendesk account: who made each change, what was changed, the action taken, and the source IP address. Audit log access requires a Zendesk Enterprise plan (or the relevant add-on).

This kit expects Zendesk audit log entries to be ingested as individual JSON objects into the `zendesk-audit` tag, pulled from the [Zendesk Audit Logs API](https://developer.zendesk.com/api-reference/ticketing/account-configuration/audit_logs/).

This kit provides the following utilities:

- Queries
    - Detections
    - Stats
- Scheduled Searches
- Dashboards
- Actionables
- Templates
- Macros
- Autoextractors

Refer to the Kit Overview playbook for more detail on these components.

**Note:** If your tag differs from the default, update both the kit's configuration macro *and* the `Tag` binding on the `zendesk-audit` autoextractor (Extractors page). The kit's queries reference fields through the autoextractor, so if it is not bound to your tag, no fields will be extracted and the queries will return empty results.

## Version History
**V1: Initial Release**
