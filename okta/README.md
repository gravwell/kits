# Okta Kit

Dashboards, detections, investigation templates, and playbooks for Okta System Log
and Okta user data in Gravwell.

The Okta Kit is licensed under the BSD 2-Clause license and the contents are
available on [GitHub](https://github.com/gravwell/kits/tree/main/okta).

There is an [Integration Guide](https://docs.gravwell.io/integrations/application/okta.html)
to help you onboard the data, and the [Okta ingester
documentation](https://docs.gravwell.io/ingesters/okta.html) covers the hosted
ingester that feeds this kit.

## Tags

The kit reads two tags, both fixed by the Gravwell Okta ingester:

| Tag | Configuration macro | Contents |
| --- | --- | --- |
| `okta` | `$OKTA` | The Okta System Log: sign-ins, MFA challenges, policy evaluations, admin actions, application access. |
| `okta-users` | `$OKTA_USERS` | Okta user profile snapshots, re-published on each poll. |

## Dependencies

- **Gravwell Network Enrichment kit** — required, and used only as a fallback.

  Okta resolves geography and network ownership itself, at the edge, at request
  time, and attaches it to most System Log events as `client.geographicalContext`
  and `securityContext`. That is better data than a local database lookup, so this
  kit takes Okta's answer whenever it is there. The Network Enrichment kit's
  `maxmind` and `asn_db` resources fill in only for the events that arrive without
  it — typically well under 1%. Every query records which source it used in a
  `geoSource` field: `okta`, `okta+maxmind`, or `maxmind`.

  This kit ships **no content from the Network Enrichment kit** — no geolocation
  databases, no copies of its resources, and not its licence. It references
  `maxmind` and `asn_db` by name and declares the dependency, nothing more. The
  GeoLite2 data and the MaxMind GeoLite2 End User Licence Agreement that governs it
  are part of the Network Enrichment kit, and you accept that licence when you
  install that kit. This kit is licensed under BSD 2-Clause, which is the only
  licence it carries.

## Configuration macros

| Macro | Purpose |
| --- | --- |
| `$OKTA` | Tag holding the Okta System Log. Default `okta`. |
| `$OKTA_USERS` | Tag holding Okta user profile snapshots. Default `okta-users`. |
| `$GRAVWELL_INSTANCE` | Base URL of this Gravwell instance, used for links in alert email. |
| `$OKTA_ALERT_SENDER` | From address for Okta alert email. |
| `$OKTA_ALERT_RECIPIENT` | To address for Okta alert email. |

Two further macros carry query logic rather than configuration, and both are fully
commented — open either one in the search GUI to read every rule:

- `$OKTA_RISK_SCORE` scores an enriched event 0-100 and buckets it into a priority.
- `$OKTA_TUNING` suppresses allowlisted accounts and addresses, and promotes
  denylisted ones.

Nothing else in the kit hides query logic behind a macro. Every query spells out
its own extraction, filtering, and enrichment so you can read what it does and
copy pieces of it.

## Alerts

Every detection routes through a single alert, **Alert - Okta - Alert Router**.
Each detection has one scheduled search, and every one of those scheduled searches
is a dispatcher on that one alert. Notification is wired up once, as a consumer.

The dispatching scheduled search's name is the alert name, so what you see in the
alert feed is the detection that produced it.

All scheduled searches and the notification flow ship **disabled**. Enable them a
few at a time and tune as you go. The **Okta Threat Overview** dashboard runs the
statistical detections interactively, so you can see what each would fire on before
you turn it on.

## Tuning

Four lookup resources control noise across every detection at once, all keyed on a
bare value — an IP address, or a lower-cased username with the email domain
stripped:

| Resource | Effect |
| --- | --- |
| `okta_user_allowlist` | Drop events involving this account, optionally until a date. |
| `okta_ip_allowlist` | Drop events from this address, optionally until a date. |
| `okta_user_denylist` | Force events involving this account to at least priority High. |
| `okta_ip_denylist` | Force events from this address to at least priority High. |

`okta_privileged_actor` and `okta_protected_target` weight sensitive accounts in
the risk score, and `okta_eventTypes` maps all ~1000 Okta event types onto a
category, a subcategory, and a "did this change configuration" flag.

## Changelog

- 2.0: Tags reduced to `okta` and `okta-users`. Every query expanded inline and
  commented; macros cut from 28 to 7. Detections ship raw entries with no render
  module so all enumerated values reach the alert. Detections consolidated onto a
  single alert router. Geography and network ownership taken from Okta's own
  client.geographicalContext and securityContext, with the Network Enrichment kit
  as a fallback only, reported per event in a new geoSource field. New detections
  for trusted origins, log stream tampering, hooks, workflows, OAuth2 clients and
  secrets, custom admin roles, device assurance, breached credentials, and user
  risk. New Okta Threat Overview dashboard.
- 1.0: Initial release.
