# Gravwell Office 365 Kit

The Gravwell Office 365 Kit provides a baseline set of queries, dashboards, templates, and investigative resources for the Office 365 cloud office suite.

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
