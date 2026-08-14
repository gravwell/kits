# Gravwell Windows Sysmon Kit

This kit contains dashboards, searches, templates, resources, playbooks, and actionables to monitor and investigate Microsoft Windows Sysmon data.

## Kit Components

### Dashboards

* `Sysmon DNS Domain Investigation` Investigate activity for a specified domain
* `Sysmon DNS Overview` Overview dashboard of DNS activity as seen by Sysmon
* `Sysmon Investigate Computer` Investigate activity on a particular computer
* `Sysmon Network Overview` Overview of network activity as seen by Sysmon
* `Sysmon Process GUID Investigation` Investigate Process Activity via Sysmon
* `Sysmon Process Name Investigator` Use the name of an EXE to search for related activity across all sysmon logs
* `Sysmon Process Overview` Sysmon Process Activity Overview
* `Sysmon Registry Overview` Activity on registry keys

### Extractors

N/A

### Macros

* `$PROVIDER` The Provider value (Default: Provider=="Microsoft-Windows-Sysmon")
* `$SYSMON` The Sysmon tag value (Default: sysmon)

### Resources

* `sysmon_event_ids` Sysmon Event IDs

### Scripts

N/A

### Searches

* `Sysmon: Computer Image Hash Totals` Total Unique Computer Images Hashes
* `Sysmon: CreateRemoteThread unique activity` Table of source applications creating remote threads in many other target applications
* `Sysmon: DNS Beaconing` Table of hosts that are queried at regular intervals
* `Sysmon: DNS Errors` Table showing DNS errors by type with description
* `Sysmon: DNS Errors Over Time` Chart categorizing the DNS errors by error type over time
* `Sysmon: DNS Most Active Clients` Table of most active DNS clients as seen by sysmon
* `Sysmon: DNS Most Active Processes` Most active DNS processes as seen by sysmon
* `Sysmon: DNS Queries by Resource Record Type` Chart of DNS Record types
* `Sysmon: DNS Queries over Time` Chart of total number DNS queries over time
* `Sysmon: DNS Requests by Computer over Time` Chart showing dns requests over time by computer
* `Sysmon: DNS Requests by Process over Time` Chart of Process DNS Requests over Time
* `Sysmon: DNS Totals` Gauge of DNS Unique Domains, Unique Queries and Total Queries
* `Sysmon: Driver Load Activity` Table of driver activity
* `Sysmon: Driver Loads with invalid signatures` Table of driver activity where the signature of a driver could not be validated
* `Sysmon: Errors` Windows Sysmon Error events
* `Sysmon: Least Common Network Service Ports` Table showing the least common network service ports
* `Sysmon: Microphone time by application` Totals up time each application spent listening to the microphone.
* `Sysmon: Most Queried DNS Names` Table of total number of queries for a given DNS Name
* `Sysmon: Network connection by IP Protocol` Chart of IPv4 vs IPv6 Connection activity
* `Sysmon: Network Connection Detected` Chart of total number of network connections over time
* `Sysmon: Network Connection Pointmap` Pointmap of network connections with ASN Organization
* `Sysmon: Network Connections` Chart of network connection counts by protocol
* `Sysmon: Network Connections by Computer` Table of total connection groups by computer
* `Sysmon: Network Peer Totals` Table of unique IPs and total connection counts by ASN Organization
* `Sysmon: Process Access with VM_WRITE Access on system32 images` Display all ProcessAccess requests where an image from outside the system32 directory accesses a process with an image inside system32 with the VM_WRITE permission bit
* `Sysmon: Process CreateRemoteThread Activity` Table of processes creating remote threads in other processes
* `Sysmon: Process Creation` Table of all Sysmon process creation events
* `Sysmon: Process Creation by User` Table of process creation event counts for interactive session 1 (the console on workstations; may be an RDP session on servers)
* `Sysmon: Process Creation Events Table as Share of Whole` Table of process creation event counts by computer with a calculation of the share of total process events across all machines
* `Sysmon: Process Creation Rate` Chart of total process creation rate
* `Sysmon: Process Creation Rates by Computer` Count of process creation events by Computer
* `Sysmon: Process Creation via Multiple Paths` Table showing a list of processes where the same image is seen executing from multiple image locations
* `Sysmon: Process Rare Extensions` Table of rare image extensions on processes
* `Sysmon: Process Start Deviation by Integrity Level` Chart showing standard deviation of the count of process starts by Integrity Level
* `Sysmon: Process Tampering Activity by Type` Chart of Sysmon process tampering events by type
* `Sysmon: Process Tampering Event Counts by Type` Table of Sysmon process tampering events by type
* `Sysmon: Process Termination by Computer` Table of Process Terminations by Computer
* `Sysmon: Rare Process Image Hashes` Table of rarely seen process SHA256 hashes
* `Sysmon: Registry Autorun` Show registry events where an autorun program is installed
* `Sysmon: Registry events by computer & image` Counts the number of registry events (creation, deletion, modification) per computer and image (executable file)
* `Sysmon: Registry Modifications by Image` Chart which programs are modifying the registry the most
* `Sysmon: Registry Overview` Chart of total registry activity
* `Sysmon: Registry Technique Frequency` Frequency of potential attack techniques via registry modification
* `Sysmon: Registry Techniques Detected` Count of triggered rules that indicate potential registry modification
* `Sysmon: Short Lived Processes` Table of short lived processes
* `Sysmon: Top 100 Parent Processes` Table of the 100 most common parent processes that execute other processes
* `Sysmon: Unique Process Creations` Table of parent processes that are only seen executing other processes once
* `Sysmon: Unsigned Driver Loads` Unsigned driver activity
* `Sysmon: Windows Low Integrity Process Starts` Table of process starts from Low Integrity Applications
* `Sysmon: Windows Product Launch Counts` Table of product launch counts
* `Sysmon: Windows Registry Environment Modification` Query to show all registry write activity to system wide environment variables
* `Sysmon: Windows Rule Tally` Table of total events by each rule technique

### Templates

* `Event Counts by ProcessGuid` Numbercard of total Event Counts by Process Guid
* `Sysmon application launches by Computer` For a given computer, list the applications launched and frequency of launches.
* `Sysmon DNS Client Querying this Name`
* `Sysmon DNS Processes Querying this Name`
* `Sysmon DNS queries by Computer` Total DNS queries by specified Computer.
* `Sysmon DNS Requests over Time`
* `Sysmon DNS Totals`
* `Sysmon EventID Frequency by Computer` Charts the frequency of various event types for a given computer.
* `Sysmon Matching SHA256 Process Creation` Show all processes that match a given SHA256
* `Sysmon network connections by Computer` For the specified Computer, find network connection counts by service.
* `Sysmon Process DNS Query Activity Summary` Table of DNS query activity for a given process
* `Sysmon Process Guid Loaded Images` Show all loaded images by a specific process
* `Sysmon ProcessGuid` Identify all other images that match the SHA256 from a process
* `Sysmon ProcessGuid DNS Activity` Show all DNS activity for a given process
* `Sysmon ProcessGuid File Delete` Show all files deleted by a specific process GUID
* `Sysmon ProcessGuid Files Created` Show all files created by a specific process GUID
* `Sysmon ProcessGuid Network Connections` Sysmon outbound process activity
* `Sysmon ProcessGuid Registry Activity`
* `Sysmon ProcessName Created` All Sysmon created events for a given process name
* `Sysmon ProcessName DNS` DNS requests by a given process name
* `Sysmon ProcessName Event Chart` A chart of all EventIDs related to a given process name
* `Sysmon ProcessName Files created` Files created by a given process name
* `Sysmon ProcessName network` Network communications from a given Image name
* `Sysmon ProcessName Users` Chart of Users who have executed this process

### Actionables

* `Process GUID` Investigate Process GUIDs
* `Sysmon Computer` Examine Sysmon activity for a Windows host
* `Sysmon DNS`
* `Sysmon Executable` Examine Windows Executable Events
* `Sysmon SHA256 Match` Search sysmon events for matches on a SHA256

### Playbooks

* `Sysmon Gravwell Kit`

## Dependencies

* `io.gravwell.windows.resource` (MinVersion 1)
* `io.gravwell.networkenrichment` (MinVersion 6)

The Windows Resource kit supplies `windows_access_flags` and `windows_error_codes`; the Network Enrichment kit supplies `dns_types`, `network_services` and the `asn_db` GeoIP database.

## Changelog

**8: Audit remediation**
- Corrected the ProcessGuid File Delete template to Event ID 23, the Sysmon Errors search (Event ID 255 emits no RuleName), and the registry Environment path literal.
- Fixed time-windowed aggregation on the Integrity Level deviation chart and the `network_services` composite join.
- Widened aggregations that discarded fields their tables named, and scoped every `kv` to the `Hashes` field.
- Added Sysmon 13/14 event IDs (26-29) to the `sysmon_event_ids` resource.
- Added a Sysmon Computer actionable feeding the Investigate Computer dashboard, and rewired four mis-pointed dashboard tiles.
- Replaced the banner and cover art with the standard Gravwell kit branding, and added a matching icon.

**6: Initial catalogued release**
