This kit is designed to provide an out-of-the-box experience for working with Teleport audit logs.

An integration guide is available on [this documentation page](https://docs.gravwell.io/integrations/application/teleport.html).

Teleport records an audit event for every cluster action: logins, interactive sessions, remote command execution, file transfers, and administrative changes to users, roles, and tokens. Each event is a single JSON object.

This kit expects Teleport audit events to be ingested into the teleport-audit tag. On self-hosted clusters the audit log is written as JSON lines under /var/lib/teleport/log/&lt;uuid&gt;/, which the Gravwell File Follower can watch directly; the Teleport Event Handler can also forward events. See the [Teleport audit log reference](https://goteleport.com/docs/reference/deployment/monitoring/audit/) for details.

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

**Note:** If your tag differs from the default, update both the kit's configuration macro *and* the Tag binding on the teleport-audit autoextractor (Extractors page). The kit's queries reference fields through the autoextractor, so if it is not bound to your tag, no fields will be extracted and the queries will return empty results.

## Changelog
**V1: Initial Release**
