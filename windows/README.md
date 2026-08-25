# Gravwell Windows Kit

This kit provides a baseline set of queries, dashboards, and investigative resources for builtin Windows audit logs.

Events are collected with the `winevent` ingester, either directly from each host or from a Windows Event Collector (WEC) subscription. See the **Windows - Windows Event Collector** playbook for a WEC walkthrough, and the **Windows - Readme** playbook for tagging guidance, required Event IDs, and example logs.

## Dependencies

This kit requires the **Windows Resources** kit:

| Kit | ID | Minimum version |
|---|---|---|
| Windows Resources | `io.gravwell.windows.resource` | 4 |

Version 4 is required because the failed-logon searches look up `windows_ticket_failure_codes`, which was not present in earlier releases.

## Tags

The kit's queries reach their data through five configuration macros. The defaults assume Security-channel events are tagged `windows_security` and System-channel events `windows_system`; change the macro values if your tags differ.

| Macro | Default | Used by |
|---|---|---|
| `WINDOWS_ALL` | `windows_*` | All Windows overview searches |
| `WINDOWS_LOGON` | `windows_security` | Logon, lockout, and pass-the-hash searches |
| `WINDOWS_GROUP` | `windows_security` | Group creation, deletion, and membership searches |
| `WINDOWS_USER` | `windows_security` | User account searches |
| `WINDOWS_EVENTLOG_CLEARED` | `windows_security,windows_system` | Event log cleared search (EventID 1102 and 104) |

## Kit Components

| Component | Count |
|---|---|
| Saved searches | 29 |
| Dashboards | 5 |
| Macros | 5 |
| Resources | 3 |
| Playbooks | 2 |
| Files | 3 |
| License | 1 |
| **Total items** | **48** |

### Dashboards

- **Windows - Overview** — event volume by tag, computer, EventID, and level
- **Windows - Logons - Successful** — successful logons, RDP logons, and administrator logons by group membership and elevated token
- **Windows - Logons - Failures/Lockouts** — failed logons, account lockouts, and failures for locked-out accounts
- **Windows - Groups - Overview** — group creation, deletion, and membership changes
- **Windows - Users - Overview** — user account creation, change, enable, disable, delete, and unlock

### Resources

Shipped with this kit:

- `windows_auth_fail_codes` — 4625 failure sub-status codes to descriptions
- `windows_event_level_criticality` — event level numbers to criticality
- `windows_eventid_messages` — Event IDs to rendered message text

Used from the `io.gravwell.windows.resource` dependency:

- `windows_login_types` — logon type numbers to names
- `windows_ticket_failure_codes` — Kerberos 4771 failure codes to descriptions

## Changelog

### v3

- Fixed `WINDOWS_EVENTLOG_CLEARED`, which expanded to two nonexistent tags and disabled the System-channel (EventID 104) half of the Event Log Cleared search.
- Fixed the builtin-user exclusion in the successful-logon overview and RDP searches, which excluded nothing and disagreed with the detail tables beneath them.
- Fixed the malformed renderer call that broke the Groups dashboard overview tile.
- Repaired a malformed record in `windows_auth_fail_codes` that could fail the whole resource load.
- Failed-logon searches now decode `SubStatus`, the field that carries 4625's actionable reason, instead of the generic `Status`.
- The pass-the-hash search now reports `EventID`, so successful and rejected attempts are distinguishable.
- Group overview no longer counts the nonexistent Event ID 4736 and now includes 4748.
- Raised the `io.gravwell.windows.resource` dependency to version 4.
- Labelled all saved searches, corrected macro and ConfigMacro descriptions, removed duplicate dashboard queries, and replaced the placeholder playbook author.

### v2

- Decoupled the kit from the Windows Resources kit: the shared lookup resources now ship in `io.gravwell.windows.resource`, which this kit declares as a dependency.
- Renamed kit components to distinguish them from the Windows Resources kit.
- Corrected `MinVersion`/`MaxVersion` bounds and ConfigMacro types, and standardised licensing.

### v1

- Initial release.
