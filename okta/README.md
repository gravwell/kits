# Okta Kit

Detections, alerts, dashboards, saved queries, templates and investigation playbooks for the
Okta System Log.

The Okta Kit is licensed under the BSD 2-Clause license and the contents are available on
[GitHub](https://github.com/gravwell/kits/tree/main/okta).

## Data

| Tag (config macro) | Default | Required | Contents |
|---|---|---|---|
| `$OKTA` | `okta` | yes | Okta System Log events, one JSON event per entry, timestamped by `published` |
| `$OKTA_USERS` | `okta-users` | no | Okta user profile records; only the user dashboards and queries use it |

The user dashboards count each user once, from their newest record in the time range.
They show the whole directory only if every user is written at least
once per dashboard time range. The Okta hosted ingester does this with a daily full snapshot
(versions after 1.0.0); version 1.0.0 only writes users when they change.

The user-directory dashboards don't search the user records. An hourly scheduled search, **Okta -
User Aggregates**, computes the directory figures from the newest record per user in the last 25
hours and saves them to the resource `okta_user_aggregates` with `table -save -update rowkey`, as
`ts,metric,key,value,rowkey` rows (`ts` is the run time in Unix seconds). It is one compound query:
`@users` reads the user tag once, one inner query per metric counts it, and the main query stacks
the results with `dump -p`. The figures cover:

- users by status, user type, division, department, job title, manager and timezone;
- last sign-in and password age of active users;
- credential providers;
- average password age and onboarding time.

**Okta User Overview**, **Okta User Authentication Overview** (except its user table) and the
timezone table on **Okta Sign-In Locations** read only that resource with `dump -r`
(for example `dump -r okta_user_aggregates metric=="status" key value`). `-update rowkey` replaces
the rows whose `rowkey` is in the new results and keeps every other row. `rowkey` is
`metric|key` for the current figures, so each run overwrites them, and `ts|metric|key` for the
`last_signin_history` and `password_age_history` rows, so each run adds one point to the two
"over Time" charts. The history is never pruned. A key that no longer occurs (a department nobody
is in any more, a status or age bucket that dropped to zero) keeps its last count, and a run that
finds no users changes nothing. The current figures don't depend on the time range; the "over
Time" charts follow it. The kit ships the resource with only its header row, so the dashboards
are empty until the first run that finds users (at install, then at minute 17 of every hour).
Upgrading the kit resets the resource and its history the same way. The search needs the daily
snapshot to count users who haven't changed, and its owner needs permission to write resources.
The aggregates only feed those dashboards. Detections never read them; they search the System
Log directly, so they work from the moment the kit is installed, with or without aggregate
history.

Both are written by the Gravwell Okta hosted ingester; see the
[Integration Guide](https://docs.gravwell.io/integrations/application/okta.html). Any other
ingest path works if each entry is one System Log event as returned by the Okta API
(`/api/v1/logs`). Change the config macros at install if your tags differ. The kit's
queries use `json`, not `ax`, so they work on any tag. The `okta` and `okta-users`
autoextractors only matter for your own `ax` searches.

## Dependencies

- Gravwell 5.10.0 or newer.
- Gravwell Network Enrichment kit (version 19 or newer), installed automatically, as a
  fallback only. Locations on the maps and in the country tables come from Okta itself
  (`client.geographicalContext` and `securityContext`), which Okta resolves when the request
  happens. The kit's location queries use the Network Enrichment kit's GeoIP database (the
  `geoip` module) only for events Okta didn't place (about 0.5% in a sample org), and records
  which source it used in `geoSource` (`okta`, `maxmind`, or `none`).

## After installing

All six alerts and their 49 scheduled searches are enabled at install. With no consumers attached,
an alert only writes its events to the tag `_alerts`, so nothing is sent anywhere until you
add one. `_alerts` is shared by every kit's alerts; the Okta kit's events have `Contents._vendor`
set to `Okta`.

1. Read the alerts. The fields are under `Contents`:
   `tag=_alerts json Contents._vendor==Okta Contents._alert_title as title Contents.context as context | table title context`.
   The Investigation dashboard's "Okta Alerts" tile does this for one actor, target or IP,
   and the **Okta Threat Overview** dashboard shows them by priority and detection.
2. To notify someone, add a consumer to the alert (Automation > Alerts): a flow that sends
   email, posts to Slack, Teams or a webhook, or opens a ticket. The kit ships no consumers
   because every team routes alerts differently.
3. Add your own administrators and service accounts to the tuning lookups (below).
4. To turn off one detection, disable its scheduled search (Automation > Scheduled Searches;
   labels `okta`, `detection` and the group, for example `authentication-sessions`). To turn
   off a whole group, disable the alert and its scheduled searches.

### Alerts

| Alert | Detections |
|---|---|
| Alert - Okta - Authentication & Sessions | 24 |
| Alert - Okta - Admin & Configuration Changes | 13 |
| Alert - Okta - Account & MFA Changes | 5 |
| Alert - Okta - Threats & Platform | 5 |
| Alert - Okta - Modification Feed | 1 |
| Alert - Okta - Kit Health | 1 |

Every detection runs every 15 minutes over the previous 15 minutes. Start minutes are
spread across the quarter hour so the searches don't all run at once. Detections that need
history look further back on their own (14 days for "Admin Console Access from a New IP",
30 days for "Sign-In by a Recently Deactivated User", 24 hours for "Admin Role Granted to a
New User", 12 hours for "Sign-In from a New IP After MFA Reset", 4 hours for "Sessions
Started from Different Geolocations"). Those look-backs scan the System Log tag every 15
minutes; on a large org, lengthen their schedules if search load matters.

### Alert events

Each security alert event carries the same fields (in `_alerts`, under `Contents`;
`Metadata` holds the alert and scheduled search that raised it):

| Field | Meaning |
|---|---|
| `_alert_title` | `Alert: Okta - System Log - <category> - <subcategory> - <priority> - <detection>` |
| `_alert_priority` | Critical (risk ≥ 90), High (≥ 75), Medium (≥ 55), Low (≥ 40), Informational |
| `_alert_name` | detection name; the key used by the tuning lookups |
| `_alert_risk` | risk score, 0-100 |
| `_vendor`, `_product` | `Okta`, `System Log` |
| `_category`, `_subcategory` | from the `okta_eventTypes` lookup |
| `user` | the person acted on if there is one, otherwise the actor |
| `src_ip` | client IP (or the first IP of the request chain) |
| `target` | the primary target: the user acted on, else the app account, else the app, else the first target |
| `eventType`, `published` | from the Okta event |
| `_mitre_tactic`, `_mitre_technique` | ATT&CK mapping |
| `context` | one readable sentence: who did what to whom, from where, with what result |

**Risk score**: every event starts from a base score for its event type (privilege
grants 90, API tokens and identity providers 85, MFA and policy changes 80, and so on).
Bumps are added for warning or error severity, a successful outcome, an anonymizing proxy,
a privileged actor or a protected target. Many detections also set a minimum (the Priority
column below), so a password spray is never reported below High.

### Detections

"In the window" means within the 15-minute search window.

#### Authentication & Sessions (24)

| Detection | Fires on | Priority | ATT&CK |
|---|---|---|---|
| Attempted Bypass of Okta MFA | `user.mfa.attempt_bypass` | by risk score | Credential Access, T1111 |
| Multiple Okta Sessions for One User from Different IPs | 2+ new sessions from 2+ IPs for one user in the window | Medium minimum | Lateral Movement, T1550.004 |
| Multiple Okta Users Authenticating from the Same Device Behind a Proxy | One device token used by 2+ users through an anonymizing proxy | High minimum | Credential Access, T1110.003 |
| Okta Admin Console Access from a New IP | Admin Console access from an IP the admin has not used for it in 14 days | Medium minimum | Initial Access, T1078.004 |
| Okta Admin Console Access via Anonymizing Proxy | Admin Console access through an anonymizing proxy | High minimum | Initial Access, T1078.004 |
| Okta Brute Force Against One Account | 5+ invalid-credential failures for one user in the window | Medium minimum | Credential Access, T1110.001 |
| Okta FastPass Phishing Detection | FastPass declined to sign in to a phishing origin | by risk score | Initial Access, T1566 |
| Okta Many Device Tokens from One IP on Failed Sign-Ins | 10+ device tokens on invalid-credential failures from one IP in the window | Medium minimum | Credential Access, T1110 |
| Okta New Admin Console Behaviours | Admin Console sign-on with a new device, IP, location or velocity flag | High minimum | Initial Access, T1078.004 |
| Okta OAuth Refresh Token Reuse Detected | Rotated refresh token presented again (org or custom authorization server) | High minimum | Credential Access, T1528 |
| Okta Password Spray from One Device | One device token failing for 3+ users in the window | High minimum | Credential Access, T1110.003 |
| Okta Password Spray from One IP | One IP failing for 3+ users in the window | High minimum | Credential Access, T1110.003 |
| Okta Session Start via Anonymizing Proxy | Session start (success or failure) through an anonymizing proxy | Medium minimum | Command and Control, T1090.003 |
| Okta Session Used from Multiple Countries | One browser session (root session ID) seen from 2+ countries; phone events ignored | High minimum | Credential Access, T1539 |
| Okta Sign-In Events via Third-Party IdP | Inbound IdP / SAML sign-in rejected (replayed or invalid assertion, unknown endpoint) | by risk score | Initial Access, T1199 |
| Okta Sign-In by a Recently Deactivated User | Successful sign-in by a user deactivated or suspended in the previous 30 days and not re-activated | Critical minimum | Initial Access, T1078 |
| Okta Sign-In from a New IP After MFA Reset | Sign-in within 12 hours of an MFA reset, from an IP not used for the reset | High minimum | Initial Access, T1078 |
| Okta Sign-In with Elevated Risk or New Behavior | Okta risk HIGH or Velocity / New Country (High), risk MEDIUM (Medium) | Medium or High minimum | Initial Access, T1078 |
| Okta User Session Impersonation | `user.session.impersonation.initiate` | by risk score | Defense Evasion, T1550 |
| Okta User Sessions Started from Different Geolocations | Sessions for one user from 2+ countries within 4 hours | High minimum | Initial Access, T1078 |
| Potential Okta MFA Bombing via Push Notifications | 5+ pushes, or 3+ pushes with 2+ denied / unanswered, for one user in the window | High minimum | Credential Access, T1621 |
| Potential Okta Password in AlternateID Field | Failed sign-in whose username is not an email address (value masked in the alert) | Medium minimum | Credential Access, T1552 |
| Potentially Successful Okta MFA Bombing via Push Notifications | Push bombing followed by a successful MFA | Critical minimum | Credential Access, T1621 |
| Unauthorized Access to an Okta Application | User tried to open an app they are not assigned to | by risk score | Initial Access, T1078 |

#### Admin & Configuration Changes (13)

| Detection | Fires on | Priority | ATT&CK |
|---|---|---|---|
| Okta API Token Created | `system.api_token.create` | by risk score | Persistence, T1136 |
| Okta API Token Revoked | `system.api_token.revoke` | by risk score | Impact, T1531 |
| Okta Admin Role Assigned to a User or Group | Admin role granted to a user, a group, or through a resource set binding | by risk score | Persistence, T1098.003 |
| Okta Admin Role Granted to a New User | Admin role granted to an account created in the previous 24 hours | Critical minimum | Persistence, T1098.003 |
| Okta Application Modified, Deactivated or Deleted | `application.lifecycle.update/deactivate/delete` | by risk score | Impact, T1489 |
| Okta Application Sign-On Policy Modified or Deleted | `application.policy.sign_on.update/delete` | by risk score | Defense Evasion, T1562 |
| Okta Identity Provider Created | `system.idp.lifecycle.create` | by risk score | Persistence, T1556.007 |
| Okta Network Zone Modified, Deactivated or Deleted | Network zone changed, deactivated, deleted or blocklist entry removed | by risk score | Defense Evasion, T1562 |
| Okta OAuth Client Secret or Credential Accessed or Created | OAuth client secret read; client credential created or activated; client privilege granted | Medium or High minimum | Credential Access, T1552 |
| Okta Policy Modified, Deactivated or Deleted | `policy.lifecycle.update/deactivate/delete` | by risk score | Defense Evasion, T1562 |
| Okta Policy Rule Modified, Deactivated or Deleted | `policy.rule.update/deactivate/delete` | by risk score | Defense Evasion, T1562 |
| Sensitive Okta OAuth Scope Granted to an App | Admin consent for a scope listed in `okta_sensitive_oauth_scopes` (exact match), or any org-level `okta.*.manage` scope | Medium or High minimum | Persistence, T1098.003 |
| Unauthorized Scope for Public App OAuth2 Token Grant with Client Credentials | Client-credentials token request refused with `no_matching_scope` | Medium minimum | Defense Evasion, T1550.001 |

#### Account & MFA Changes (5)

| Detection | Fires on | Priority | ATT&CK |
|---|---|---|---|
| High Number of Okta Password Reset or Unlock Events for One User | 3+ password reset / unlock events for one user in the window | Medium minimum | Credential Access, T1110 |
| Locked Out or Account Locked | Account lockouts (`user.account.lock`, `user.account.lock.limit`) | by risk score | Credential Access, T1110 |
| New Okta User Created | `user.lifecycle.create` | by risk score | Persistence, T1136.003 |
| Okta MFA Reset or Deactivated | MFA factor deactivated or all factors reset | by risk score | Persistence, T1556.006 |
| User Reported Suspicious Activity | End user reported suspicious activity | by risk score | Initial Access, T1078 |

#### Threats & Platform (5)

| Detection | Fires on | Priority | ATT&CK |
|---|---|---|---|
| Okta Protected Action Attempted or Request Blocked | `security.protected_action.attempt`, `security.request.blocked` | Medium minimum | Initial Access, T1078 |
| Okta Security Threat Detected | `security.threat.detected` (ThreatInsight) | by risk score | Credential Access, T1110 |
| Okta Support Access to the Org | Okta Support viewed or changed the org, or was granted impersonation | Medium minimum | Initial Access, T1199 |
| Okta ThreatInsight Threat Suspected Promotion | Any event with `debugData.threatSuspected` true | by risk score | Credential Access, T1110 |
| Possible Okta DoS Attack | Rate-limit and concurrency-limit violations | Medium minimum | Impact, T1498 |

#### Modification Feed (1)

| Detection | Fires on | Priority |
|---|---|---|
| Risk-Scored Modification Feed | Every configuration or account change scoring Low (40) or above; at most 50 events per run | Low and above |

The modification feed is a review queue, not a detection. It overlaps with the Admin &
Configuration Changes detections and is noisier; if you attach a notification to it, expect
more volume than from the other alerts, or disable it if you only want detections.

#### Kit Health (1)

| Detection | Fires on | Priority |
|---|---|---|
| Target Key Order Changed | Okta changed how target objects are serialized (see Known assumptions) | Critical |

## Tuning

All tuning is in lookup resources (Resources page). Rows ship disabled (`enabled` = 0) as
examples. Logins are compared without the `@domain` part and in lowercase.

| Lookup | Key | Effect |
|---|---|---|
| `okta_user_allowlist` | `<login>\|<detection name>` or `<login>\|*` | drop alerts where this account is the actor or the person acted on; optional expiry `until_ymd` (YYYYMMDD) |
| `okta_ip_allowlist` | `<ip>\|<detection name>` or `<ip>\|*` | drop alerts from this source IP; optional expiry |
| `okta_user_denylist` | same as the user allowlist | raise to at least High, optionally only when the risk score ≥ `min_risk` |
| `okta_ip_denylist` | same as the IP allowlist | raise to at least High, optionally only when the risk score ≥ `min_risk` |
| `okta_privileged_actor` | `account` | add `actor_weight` to the risk score when this account acts |
| `okta_protected_target` | `account` | add `target_weight` when this account is acted on (never when it acts on itself) |
| `okta_sensitive_oauth_scopes` | `scope` | scopes that make "Sensitive Okta OAuth Scope Granted to an App" fire, with tier High or Medium; tier `None` silences a scope |
| `okta_eventTypes` | `eventType` | category, subcategory and whether the event type is a modification |

The detection name is the part of the scheduled search name after the group, for example
`jsmith|Okta Admin Console Access from a New IP`. To change a threshold or the schedule,
edit the saved query or the scheduled search (an upgrade of the kit replaces your edits).
"Search - Okta - Kit Health - Event Types Missing from Lookup" lists event types in your
data that `okta_eventTypes` doesn't know about yet.

## Known assumptions

- **Target serialization.** An Okta event has one actor and a list of targets (users, apps,
  app accounts, groups, policies...). The kit reads targets by type with a regular
  expression rather than splitting the list, so every event stays one row and no alert is
  counted once per target. This relies on Okta writing each target's keys in the order
  `id, type, alternateId, displayName`, which held for every target in 90 days of
  production data. If Okta ever changes that order, the typed target fields
  (`targetUser*`, `targetAppUser*`, `targetApp*`) come back empty and detections fall back
  to the first target. The **Kit Health - Target Key Order Changed** alert fires
  (Critical) as soon as one event in the window doesn't match; report it to the kit
  maintainers.
- **Window and ingest delay.** A detection only sees events whose `published` time falls in
  its 15-minute window at the moment it runs. Events that arrive after the window has been
  searched are not alerted on. If your ingester routinely lags by minutes, lengthen the
  scheduled search duration (with some duplicate alerts as the cost).
- **Okta-side features.** Some detections depend on Okta features your org may not have
  (ThreatInsight, FastPass, behavior detection and risk scoring, Okta Support access
  logging). They stay silent rather than failing when the events are absent.

## Tests

`tests/okta_fixtures.py` holds synthetic Okta events (example.com users, documentation
IP ranges) for every detection, including cases that must not fire. It imports them into a
separate tag, runs every detection over every case's 15-minute window on a Gravwell
instance with the kit installed, and checks that exactly the expected detections fire. See
`tests/README.md`.

## Changelog

- 1.0: Initial release.
  - 49 detections grouped into 6 alerts (5 security alerts plus Kit Health), each detection a
    producer on its alert, all enabled at install. Alert events go to `_alerts` with a
    common field set.
  - Detections every 15 minutes; one risk score with per-detection
    minimum priorities; ATT&CK labels; tuning lookups for users, IPs, privileged accounts
    and OAuth scopes.
  - Dashboards: General, Category, Event Type, Actor/Target, Investigation, User,
    User Authentication overviews (both from hourly pre-computed aggregates in the
    `okta_user_aggregates` resource, written by the "Okta - User Aggregates" scheduled search), Sign-In Locations
    (maps and per-country tables) and
    Threat Overview (the alerts raised, plus the signals the statistical detections watch,
    ranked without thresholds); locations from Okta's own geolocation;
    20 templates; 3 actionables (actor, target, IP) that open the Investigation dashboard,
    which includes the alerts and sign-in locations for that actor, target or IP.
  - Playbooks: kit overview and alert response.
