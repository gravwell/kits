# Kit for pihole

The pihole kit includes everything to pull, extract and query the query data from your pihole server. 


## Kit Components

### Dashboards

`Pihole Overview` pihole query overview. Mirrors the data in the pihole admin homescreen 

### Extractors

`pihole-query`

### Macros

`$PIHOLE_DNS_QUERY` All in one query that extracts and performs the needed lookups to translate the codes to statuses

### Config Macros

`$PIHOLE_APIKEY` sets the API key for the script

`$PIHOLE_IP` Set the IP address for the pihole instance

`$PIHOLE_PORT` Sets the port for the pihole instance (Usually 80)

### Resources
`pihole-replytypes` pihole return types

`pihole-rectypes` DNS Record Types

`pihole_status_codes` Query Statuses

### Scripts

`PiHole Script` Gathers the data from the pihole API and creates entries in Gravwell 

### Searches
N/A

### Playbooks
N/A


## Install Instructions
1. Set the `$PIHOLE_IP` macro to the IP Address of your pihole instance
2. Change the `$PIHOLE_PORT` macro to the port of your pihole instance.(Usually 80)
3. Get the API key from your pihole instance. Go to `Settings > API` and then the `Show API` token button
4. Set the `$PIHOLE_APIKEY` macro to the token from the previous step.
5. Set the `PIHOLE_TAG` macro to the desired tag name. The defualt is `pihole-queries`.
6. If you used a tag name other than the defualt you will need to update the extractor to your new tag name. 
7. Go to scripts and enable the `PiHole Script` to run every 5 minutes with a cron schedule of `*/5 * * * *`

## Query Data
Data will be located in the `pihole-queries` tag and can be accessed by going to Query Studio and using the query `tag=pihole-queries`

For data that is extracted and had the lookups attached change your query to `$PIHOLE_DNS_QUERY`


## Release Notes
## [v2](https://github.com/gravwell/kits/tree/main/pihole) (2023-11-8)


### Upgrade Steps
* Required to overwrite the `$PIHOLE-DNS-QUERY` to take advantage of the updated and corrected resource files

### New Features
* Added three configuration macros to enable the data pull script
* Added the data pull script `PiHole Script`. Allows data to be pulled from a pihole server with minimum configuration

### Bug Fixes
* Replaced the original resource files with new copies that fixed some small errors in lookups.


## Copyright

PiHole logo Copyright Pi-hole. Licensed under CC BY-SA 4.0
