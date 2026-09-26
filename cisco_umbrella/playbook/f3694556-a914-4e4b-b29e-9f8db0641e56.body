This kit is designed to provide an out-of-the-box experience for working with Cisco Umbrella logs.

Cisco Umbrella exports its logs as CSV files to an Amazon S3 bucket (either Cisco-managed or self-managed). This kit expects those logs to be ingested into three tags, one per log source:

- DNS logs (`umbrella-dns`) - traffic that reached the Umbrella DNS resolvers
- Proxy logs (`umbrella-proxy`) - traffic that passed through the Umbrella intelligent proxy
- Admin audit logs (`umbrella-audit`) - changes made in the Umbrella dashboard by your administrative team

Log format references:

- [DNS Log Formats](https://securitydocs.cisco.com/docs/umbrella-dns/olh/147415.dita)
- [Proxy Log Formats](https://securitydocs.cisco.com/docs/umbrella-dns/olh/147416.dita)
- [Admin Audit Log Formats](https://securitydocs.cisco.com/docs/umbrella-dns/olh/147414.dita)

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

**Note:** If your tags differ from the defaults, update both the kit's configuration macros *and* the `Tag` binding on the matching autoextractors (Extractors page). Umbrella logs are headerless CSV, so if an autoextractor is not bound to your tag, no fields will be extracted and the kit's queries will return empty results.

## Version History
**V1: Initial Release**
