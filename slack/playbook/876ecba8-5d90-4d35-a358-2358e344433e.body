This kit is designed to provide an out-of-the-box experience for working with Slack audit logs.

The Slack Audit Logs API records administrative and security-relevant actions across an Enterprise Grid organization: logins, role and permission changes, app installations, file activity, workspace exports, and hundreds of other actions. Audit log access requires an Enterprise Grid plan.

This kit expects Slack audit log entries to be ingested as individual JSON objects into the `slack-audit` tag, pulled from the [Slack Audit Logs API](https://docs.slack.dev/admins/audit-logs-api).

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

**Note:** If your tag differs from the default, update both the kit's configuration macro *and* the `Tag` binding on the `slack-audit` autoextractor (Extractors page). The kit's queries reference fields through the autoextractor, so if it is not bound to your tag, no fields will be extracted and the queries will return empty results.

## Version History
**V1: Initial Release**
