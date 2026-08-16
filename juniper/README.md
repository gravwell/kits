# Gravwell Juniper Kit
****

The Gravwell Juniper Kit provides a baseline set of queries, dashboards, templates, and investigative resources for Juniper devices.

*Desired format and delivery method: syslog*

##Kit Components
****

<font color="orange">Dashboards</font>

`Juniper Overview` Overview of Juniper alarms and user logins

`Juniper User Detail` User commands, configuration changes, and login details

`Juniper User Overview` Overview of user commands, configuration changes, and logins

<font color="orange">Query Library</font>

`Juniper Logins` List of user logins

`Juniper Login Count by Hostname` Count logins by hostname

`Juniper Logins by Client Mode` Count logins by client mode

`Juniper CLI Logins by User (mgd)` Count UI_LOGIN_EVENT CLI logins by user, as reported by mgd

`Juniper SSH Logins by User (sshd)` Detail sshd accepted logins by user and unique source, across all authentication methods

`Juniper SSH Login Count by User (sshd)` Count sshd accepted logins by user, across all authentication methods

`Juniper Failed Logins by Src` Count failed login attempts by source with a count unique usernames and destinations

`Juniper Failed Logins by Destination` Count failed login attempts by destination with a count unique usernames and sources

`Juniper Command Count` Count by command

`Juniper Latest Commands` Display commands per user hostname

`Juniper Configuration Changes by Hostname` Count configuration changes by hostname

`Juniper Latest Configuration Changes` Display configuration changes per user

`Juniper Configuration Errors` Display configuration errors by hostname

`Juniper Alarms` Detail alarms by set, class, reason

`Juniper Alarms Overview` Count alarm by hostname, alarm set, color, class, reason

`Juniper Alarms by Hostname` Count alarms by hostname

`Juniper Alarms by Class` Count by alarm class

`Juniper Alarms by Set` Count by alarm set

`Juniper Alarms Count by Color` Count by alarm color

`Juniper Facility Count` Count by logging facility

`Juniper Appname Count` Count by appname

<font color="orange">Extractors</font>

`juniper_tag` Syslog extraction for tag juniper

<font color="orange">Macros</font>

`$JUNIPER_TAG` Set juniper tag name (CONFIG MACRO)

`$JUNIPER_LOGIN_HELPER` Shared regular-expression extractions for Juniper login events

<font color="orange">Resources</font>

`juniper_facility` Juniper facility details

`juniper_severity` Juniper severity details

`juniper_logins_exclusion_list` Users excluded from the failed-login searches

<font color="orange">Templates</font>

`Juniper Config Set` Display configuration set per user, hostname

`Juniper User Commands` Display executed commands per user, hostname

`Juniper User Logins` Display logins per user, hostname

`Juniper User Config Mode` Display users entering config mode per user, hostname

<font color="orange">Playbooks</font>

`Juniper Kit` Resources for understanding Juniper log data

##Install Instructions
****

*After verifying Juniper data is being properly indexed and available for search*

1. Set the `$JUNIPER_TAG` macro to the tag containing juniper data

2. Populate the `juniper_logins_exclusion_list` resource with any service accounts that should be excluded from the failed-login searches. The resource ships with the header row `excluded_users` and no entries, which excludes nothing.

*Note: the kit's autoextractor is bound to the tag name `juniper`. If your Juniper data lands on a different tag, update the autoextractor's tag after install as well as the `$JUNIPER_TAG` macro — every query in this kit uses `ax`, which needs an autoextractor bound to the tag actually in use.*

##Changelog
****

**6: Audit remediation**

- Rewrote the Command Count and Latest Commands searches, which filtered syslog facility 4 (authorization) and matched a message shape Junos does not emit. Both now read `UI_CMDLINE_READ_LINE` from `mgd`, and parameterless commands such as `commit` match.
- Added the missing `UI_LOGIN_EVENT` filter to Login Count by Hostname, which counted every `mgd` event.
- Restored the commented-out `Alarm set:` filter on Alarms by Hostname, which was counting cleared alarms and alarmd chatter.
- Widened the shared login regex to accept an empty `ssh-connection`, so console, serial and telnet logins are no longer discarded.
- Widened the sshd searches to match `publickey` and `keyboard-interactive` logins, not only `password`.
- Carried the facility name and description through the aggregation on Facility Count, which had rendered both columns empty.
- Removed the undocumented `Severity != 6` exclusion from both failed-login searches, which could discard the events they exist to find.
- Repaired both dashboards: removed three search slots referencing GUIDs that exist nowhere, dropped a search no tile displayed, and renumbered every affected tile index.
- Standardised the alarm regex across all five alarm searches, so the same alarm no longer groups under two different names, and alarm ids of 10 or above parse correctly.
- Corrected the `juniper_logins_exclusion_list` header, which declared a phantom second column, and its stale `Size`/`Hash`.
- Renamed the three overlapping SSH login items to name their source, fixed two typos in shipped item names, surfaced `Client_Mode` in the failed-login tables, removed dead lookups and extractions, added missing labels, and repaired five malformed links in the playbook.
- Replaced the kit art with the standard Gravwell branding: the icon, banner and cover were five byte-identical copies of one 640x426 photograph, and the `cover.png` symlink pointed at the icon.
