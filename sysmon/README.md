# Gravwell Windows Sysmon Kit

This kit contains dashboards, searches, resources, and actionables to monitor and investigate Microsoft Windows Sysmon data.

## Kit Components

### Dashboards

* `Sysmon Network Overview` Overview dashboard of network activity by Sysmon
* `Sysmon DNS Overview` Overview dashboard of DNS activity by Sysmon
* `Sysmon investigate Computer` Investigate activity on a particular computer.
* `Sysmon Process Overview` Sysmon Process Activity Overview
* `Sysmon Registry Overview` Activity on registry keys
* `Sysmon Process GUID Investigation` Investigate Process Activity via Sysmon
* `Sysmon Process Name Investigator` Use the name of an exe to search for related activity across all sysmon logs
* `Sysmon DNS Domain Investigation` Investigate activity for a specified domain.

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

* `Sysmon: Process Creation` Table of all Sysmon process creation events
* `Sysmon: CreateRemoteThread unique activity` Table of source applications creating remote threads in many other target applications
* `Sysmon: DNS Requests by Computer over Time` Chart showing dns requests over time by computer
* `Sysmon: rare process image hashes` Table of rarely seen process SHA256 hashes
* `Sysmon: Microphone time by application` Totals up time each application spent listening to the microphone
* `Sysmon: Process Start Deviation by Integrity Level` Chart showing standard deviation of the count of process starts by Integrity Level
* `Sysmon: DNS Errors` Table showing DNS errors by type with description
* `Sysmon: Driver Loads with invalid signatures` Table of driver activity where the signature of a driver could not be validated
* `Sysmon: Windows Product Launch Counts` Table of product launch counts
* `Sysmon: Windows Low Integrity Process Starts` Table of process starts from Low Integrity Applications
* `Sysmon: Registry Techniques Detected` Table of triggered rules that indicate potential registry modification
* `Sysmon: Process Creation Rate` Chart of total process creation rate
* `Sysmon: Network Connections` Chart of network connection counts by protocol
* `Sysmon: Network Connections by Computer` Table of total connection groups by computer
* `Sysmon: Process Access with VM_WRITE Access on system32 images` Display all ProcessAccess requests where an image from outside the system32 directory accesses a process with an image inside system32 with the VM_WRITE permission bit.
* `Sysmon: Top 100 Parent Processes` Table of the 100 most common parent processes that execute other processes
* `Sysmon: DNS Queries by Resource Record Type` Chart of DNS Record types
* `Sysmon: Registry events by computer \u0026 image` Counts the number of registry events (creation, deletion, modification) per computer and image (executable file).
* `Sysmon: Unsigned Driver Loads` Unsigned driver activity
* `Sysmon: DNS Most Active Clients` Table of most active DNS clients as seen by sysmon
* `Sysmon: DNS Totals` Gauge of DNS Unique Domains, Unique Queries and Total Queries
* `Sysmon: Process Termination by Computer` Table of Process Terminations by Computer
* `Sysmon: DNS Queries over Time` Chart of total number DNS queries over time
* `Sysmon: Windows Registry Environment Modification` Query to show all registry write activity to system wide environment variables
* `Sysmon: Errors` Windows Sysmon Error events
* `Sysmon: Network connection by IP Protocol` Chart of IPv4 vs IPv6 Connection activity
* `Sysmon: Process Rare Extensions` Table of rarely image extensions on processes
* `Sysmon: DNS Errors Over Time` Chart categorizing the DNS errors by error type over time
* `Sysmon: Process Creation Via Multiple Paths` Table showing a list of processes where the same image has is seen executing from multiple image locations
* `Sysmon: Process Creation Events Table as Share of Whole` Table of process creation event counts by computer with a calculation of the share of total process events across all machines
* `Sysmon: Process Tampering Event Counts by Type` Table of Sysmon process tampering events by type
* `Sysmon: DNS Beaconing` Table of hosts that are queried at regular intervals
* `Sysmon: Short Lived Processes` Table of short lived processes
* `Sysmon: Unique Process Creations` Table of parent processes that are only seen executing other processes once
* `Sysmon: Process Creation by User` Table of process creation event counts by physical users
* `Sysmon: Windows Rule Tally` Table of total events by each rule technique
* `Sysmon: Network Connection Pointmap` Pointmap of network connections with ASN Organization
* `Sysmon: DNS Requests by Process over Time` Chart of Process DNS Requests over Time
* `Sysmon: Least Common Network Service Ports` Table showing the least common network service ports
* `Sysmon: DNS Most Active Processes` Most active DNS processes as seen by sysmon
* `Sysmon: Process Creation Rates by Computer` Count of process creation events by Computer
* `Sysmon: Process Tampering Activity by Type` Chart of Sysmon process tampering events by type
* `Sysmon: Network Connection Detected` Chart of total number of network connections over time
* `Sysmon: Process CreateRemoteThread Activity` Table of processes creating remote threads in other processes
* `Sysmon: Registry Modifications by Image` Chart which programs are modifying the registry the most.
* `Sysmon: DNS Most Queried DNS Names` Table of total number of queries for a given DNS Name
* `Sysmon: Registry Autorun` Show registry events where an autorun program is installed
* `Sysmon: Registry Technique Frequency` Frequency of potential attack techniques via registry modification.
* `Sysmon: Driver Load Activity` Table of driver activity
* `Sysmon: Registry Overview` Chart of total registry activity
* `Sysmon: Network Peer Totals` Table of unique IPs and total connection counts by ASN Organization

### Playbooks

* `Sysmon Gravwell Kit` Intro to Gravwell Sysmon Kit
