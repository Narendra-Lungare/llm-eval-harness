# Blob versioning

Blob versioning keeps an automatic previous version of a blob every time it is
overwritten or deleted. When versioning is enabled, the service creates a new
version with a unique version ID on each write; the client does not have to take
a snapshot first. Reads without a version ID return the current version.

Versions are addressed by appending the version ID to the blob URL as a query
parameter. Listing a blob with versions included returns every version with its
timestamp, so a caller can roll back by copying an older version over the
current blob or by promoting it directly.

Versioning and snapshots solve overlapping problems differently. A snapshot is
created explicitly by the client and is read-only from that point; a version is
created by the service on every write and represents what the blob looked like
after that write. Enabling versioning therefore captures writes that a snapshot
workflow would miss, at the cost of storing every version.

Deleting a blob while versioning is enabled creates a delete marker as the
current version; the previous versions remain readable. Permanently removing
data requires deleting individual versions. Versioning also changes the
behaviour of soft delete, because both features retain data independently.

_Hand-written sample fixture for smoke tests, not a copy of Microsoft
documentation._
