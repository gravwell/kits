# Gravwell Zeek Kit

The Gravwell Zeek Kit provides a baseline set of queries, dashboards, templates, and investigative resources for the Zeek Network Security Monitor.

Zeek is a powerful network monitoring platform designed to provide passive introspection into a variety of network applications and protocols.

## Zeek Configuration

This kit assumes a Zeek configuration similar to the file follower configuration found in the Zeek Docker container distributed by Gravwell.  The Docker image can be found on [Docker Hub](https://hub.docker.com/r/gravwell/Zeek).

If you already have a functioning Zeek environment you can grab our standard Zeek File Follower configuration on GitHub via [this gist](https://gist.github.com/gravwell/ddea90e22887d498afecadb86ba0a28d).

### Ingester Configuration

The Zeek kit includes a set of autoextractors to help with the processing of various Zeek data sources.  Autoextractors expect that data sources are tagged appropriately, which requires that the [File Follower](https://docs.gravwell.io/#!ingesters/file_follow.md) ingester apply the appropriate tags to each Zeek file source.

The autoextractors are available on [Github](https://github.com/gravwell/autoextractors/blob/master/Zeek/Zeek.ax).

# Well Configuration

The Zeek data set contains many highly orthogonal data sources, including unique identifiers, GUIDs, floating point timestamps, and IPv6 addresses.  To ensure that Gravwell performs well and minimizes memory usage when indexing Zeek data we highly recommend a separate well for the Zeek data with specific indexing options.

Gravwell supports two indexing engines designed to provide different capabilities and trade-offs.  Both engines can perform very well with the Zeek datasets.  The bloom engine can provide a balance of good performance and minimal disk usage while the index engine provides precise indexing performance in exchange for greater disk and memory usage.  Regardless of the chosen engine, Gravwell recommends that Zeek data be fulltext indexed with the "ignoreFloat" and "ignoreUUID" options.  The following well configurations work well with Zeek data:

## Bloom Engine
```
[Storage-Well "Zeek"]
	Location=/opt/gravwell/storage/Zeek
	Tags=Zeek*
	Accelerator-Name=fulltext
	Accelerator-Args="-ignoreFloat -ignoreUUID"
	Accelerator-Engine-Override=bloom
```

## Index Engine
```
[Storage-Well "Zeek"]
	Location=/opt/gravwell/storage/Zeek
	Tags=Zeek*
	Accelerator-Name=fulltext
	Accelerator-Args="-ignoreFloat -ignoreUUID"
	Accelerator-Engine-Override=index
```

# Additional Info
The "Zeek" and "Bro" names are owned by the [Zeek Community](https://Zeek.org).

Zeek is a [BSD](https://github.com/Zeek/Zeek/blob/master/COPYING) licensed open source project available on [Github](https://github.com/Zeek/Zeek).
