# Grok info
The Grok kit provides some documentation and a pattern resource file to allow usage of Grok patterns for data extraction within Gravwell. This *greatly* simplifies extractions that would otherwise use regular expressions directly.

Compare parsing Apache combined log entries with grok:

```tag=apache grok %{COMBINEDAPACHELOG} | table```

against parsing them with an explicit regular expression:

```tag=apache regex \"(?P<ip>\\S+) (?P<remote_log_name>\\S+) (?P<userid>\\S+) \\[(?P<date>\\S+) ?(?P<timezone>\\S+)?\\] \\\"(?P<request_method>\\S+) (?P<path>\\S+) (?P<request_version>HTTP/\\d+\\.?\\d*)?\\\" (?P<status>\\d+) (?P<length>\\d+) \\\"(?P<referrer>[^\\\"]+)\\\" \\\"(?P<user_agent>[^\\\"]+)\\\"\"
| table```

###Dependencies:
None

(Cover photo by [Waldemar Brandt](https://unsplash.com/@waldemarbrandt67w?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on Unsplash)