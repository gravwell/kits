This kit provides an out-of-the-box experience for working with Suricata EVE JSON logs.

It provides the following utilities:
- Search library queries covering alerts, DNS, TLS, HTTP, SSH, flow, fileinfo, and anomaly events
- Detections driven by scheduled searches (shipped disabled; enable and tune thresholds after install)
- Overview, alert, and protocol dashboards
- Investigative dashboards for IP and alert-signature pivots, driven by templates
- A SURICATA config macro to point the kit at your Suricata tag

Suricata should be configured for EVE JSON output, ingested into the tag named by the SURICATA macro (default: suricata). Some searches rely on optional Suricata features noted in their descriptions (anomaly and ja3 event logging; the TLS SNI and TLS version searches require extended: yes under eve-log types.tls, since basic TLS logging emits only subject and issuerdn; the file-magic searches additionally require force-magic: yes under eve-log types.files and a Suricata built with libmagic support).

The Suricata kit is licensed under the BSD 2-Clause license and the contents are available on [Github](https://github.com/gravwell/kits/tree/main/suricata).

## Dependencies
- Gravwell Network Enrichment Kit (io.gravwell.networkenrichment), installed automatically. The External Alert Sources map on the Alert Activity dashboard uses the geoip module and needs this kit, or your own MaxMind GeoIP database, to render.

## Changelog
**1.0: Initial Release**
- dashboard (5)
- file (3)
- license (1)
- macro (1)
- scheduled searches (12)
- searchlibrary (31)
  - detection queries (12)
  - dashboard searches (19)
- template (11)
