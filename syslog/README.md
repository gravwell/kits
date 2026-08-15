# Gravwell Syslog Kit

The Syslog kit contains an overview dashboard and some investigative dashboards for easily viewing syslog activity.

This kit is intended as a "getting started with syslog". It does not attempt to analyze any of the content in the actual syslog Message as the author does not know what syslog you are collecting.

Look for syslog derivative kits such as the Linux Syslog kit (io.gravwell.linuxsyslog).

## Dependencies

None. Requires Gravwell 5.4.0 or later.

## Changelog

### Version 7

- Added the BSD 2-Clause license item and refreshed its copyright year.
- Set MaxVersion to 5.99.99.
- Added a `Readme` to the MANIFEST so the in-product readme pane is populated.
- Replaced the banner and cover art with the standard Gravwell kit branding, and added a matching icon so the kit no longer uses its full-size cover image as its icon.
- Fixed the "Critical and Errors" numbercard, which aggregated by Severity and so displayed one severity's count instead of the total. Renamed it "Num Errors and Above" to match what `Severity < 4` actually selects.
- Renamed the "unparsable" search, template and dashboard tiles to "missing Hostname" — the syslog module drops entries it cannot parse, so these only ever showed valid entries with no Hostname — and widened the filter to catch the RFC 5424 NILVALUE (`-`) as well as the empty string.
- Added the `syslog_severity` lookup to the severity charts on the investigate Host and investigate SRC dashboards, and to the three tables that showed Severity as a bare integer, so severities render as text everywhere.
- Added an ordering stage to "last 100 results", which previously applied a bare `limit`.
- Corrected the "Syslog investigate SRC" dashboard description, which described sysmon activity.
- Tightened the Appname/Hostname actionable trigger, which matched empty cells, bare integers and IPv4 addresses.
- Removed authoring-instance export residue (7 `searchID`, 2 `lastDataUpdate`) from three dashboards, dropped unused field extractions from two stackgraph searches, described two templates that shipped a blank description, corrected the `syslog_facility` resource description, and zeroed the one stale item hash.

### Version 6

- Migrated saved searches to the query library and added syslog labels.
- Added the missing template for the "Syslog investigate SRC" dashboard.
