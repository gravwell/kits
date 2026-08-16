# Gravwell Office 365 Kit

The Gravwell Office 365 Kit provides a baseline set of queries, dashboards, templates, and investigative resources for the Office 365 cloud office suite. It covers Azure AD sign-in activity, Exchange mailbox and mail-flow events, SharePoint file and sharing activity, and the General (Security & Compliance) audit feed.

## Office 365 Ingester Configuration

For full ingester configuration please refer to the [ingester documentation page](https://docs.gravwell.io/ingesters/o365.html).


## Well Configuration
```
[Storage-Well "O365"]
	Location=/opt/gravwell/storage/office365
	Tags=365*
	Accelerator-Name=fulltext
	Accelerator-Args="-ignoreFloat -ignoreUUID"
```

## Tags and Autoextractors

Queries, templates, and dashboards reach their data through four config macros — `$365-AZURE`, `$365-EXCHANGE`, `$365-SHAREPOINT`, and `$365-GENERAL` — which you can repoint at your own tag names at install time.

The kit's autoextractors, by contrast, bind to the default tag names (`365-azure`, `365-exchange`, `365-sharepoint`, `365-general`) because the autoextractor item type takes a literal tag rather than a macro. If you retag your Office 365 feed, the queries follow your macro overrides but the autoextractors will not: update each autoextractor's tag in the UI after install, or the interactive auto-extraction of fields for those tags will not apply.

## Lookup Resources

Three lookup tables ship with the kit and can be used in your own searches:

| Resource | Resolves | Helper macro |
|---|---|---|
| `o365_audit_recordtype` | numeric `RecordType` to its name | `$RESOLVE_O365_RECORDTYPE` |
| `o365_audit_usertype` | numeric `UserType` to its name | `$RESOLVE_O365_USERTYPE` |
| `o365_audit_applicationid` | `ApplicationId` GUID to an application name | none — use `lookup -r o365_audit_applicationid ApplicationId id name as Application` |

## Dependencies

- `io.gravwell.networkenrichment` (MinVersion 14) — supplies the `asn_db` resource used by the ASN and geolocation lookups on the login-activity map and the login-ratio table.

## Changelog

**5: Audit remediation**
- Corrected the `365-exchange` autoextractor, which shipped as a byte-for-byte copy of `365-azure` (same name, tag, and UUID) and was never declared in the manifest. It now carries Exchange fields, its own UUID, and a manifest entry.
- Fixed the SharePoint tag macro, whose `.meta` declared the name `O365-SHAREPOINT` while every reference used `365-SHAREPOINT` — the entire SharePoint half of the kit resolved against a macro the user could not configure.
- Fixed the Azure "Active Users" numbercard, which filtered `ResultStatus == "Success"`; the Management Activity API emits `Succeeded`.
- Corrected the login-failure table, which dropped `UserType` at the aggregation and then looked it up and displayed it; the attachment-extension donut, which case-folded after grouping; the General ThreatIntel chart, which filtered a RecordType name as a `Workload` value; and the Exchange IP template, which grouped on `LogonError`, an Azure AD-only field.
- Guarded the login-ratio calculation against a zero success count, which produced `+Inf`/`NaN` for exactly the password-spray rows the table exists to rank.
- Renamed "ThreatManagement Alerts" to "Security & Compliance Alerts" to match what `RecordType==40` actually returns, and "Active Users" to "Active Mail Users" to match what the domain regex actually counts.
- Removed two duplicate manifest declarations and a searchlibrary copy of the scheduled login-history search that overwrote the scheduled job's resource when run by hand.
- Replaced inlined `lookup -r` stages with the `$RESOLVE_O365_RECORDTYPE` and `$RESOLVE_O365_USERTYPE` macros the kit already shipped.
- Corrected dashboard search aliases, pruned three dead search entries, removed authoring-instance `searchID` residue, renamed the Azure-labelled pivot that targets an Exchange template, added workload labels to every searchlibrary item, and filled in empty names and descriptions.
- Replaced the stub `MANIFEST.Readme` with this document, and added the standard kit branding art (banner, cover, icon).

**4: Prior release**
