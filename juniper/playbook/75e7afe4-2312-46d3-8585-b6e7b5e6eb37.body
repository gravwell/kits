# Gravwell Juniper Kit
****

This kit is designed to provide an out-of-the-box experience for working with Juniper logs.

An integration guide is available on [this documentation page](https://docs.gravwell.io/integrations/network/juniper.html)

This kit provides the following utilities:

- Queries
    - Detections
    - Stats
- Dashboards
- Templates
- Macros

Refer to the Kit Overview playbook for more detail on these components.

## Dependencies
None

## Changelog:
****

**v6: Audit remediation**

- Adds: Kit Overview and Copy of Readme playbooks
- Fixes: Command Count and Latest Commands now match real Junos **UI\_CMDLINE\_READ\_LINE** events (previously matched a message shape Junos never emits)
- Fixes: Login Count by Hostname no longer counts every **mgd** event (was missing a **UI\_LOGIN\_EVENT** filter)
- Fixes: Alarms by Hostname no longer counts cleared alarms and alarmd chatter (restored a dropped filter)
- Fixes: shared login regex no longer discards console, serial, and telnet logins (empty **ssh-connection** case)
- Fixes: sshd searches now match **publickey** and **keyboard-interactive** logins, not only **password**
- Fixes: Facility Count's name and description columns no longer render empty
- Fixes: failed-login searches no longer silently exclude **Severity != 6** events
- Fixes: both dashboards' broken tile references (GUIDs that don't exist, an undisplayed search, misnumbered tiles)
- Fixes: alarm regex inconsistent across all 5 alarm searches (duplicate alarm names, IDs 10 and above failing to parse)
- Fixes: **juniper\_logins\_exclusion\_list**'s malformed header and stale Size/Hash
- Fixes: two typos in shipped item names; five malformed playbook links
- Changes: renamed 3 overlapping SSH login items to name their source; surfaced **Client\_Mode** in failed-login tables; removed dead lookups/extractions; added missing labels
- Changes: kit branding images (icon, banner, cover) replaced with standard Gravwell art
