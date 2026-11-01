# Message sessions

A session groups related messages so that they are processed in order by a
single receiver. Sessions are enabled per entity: a queue or subscription must
have the session requirement turned on, and only session-aware clients can use
it. Turning sessions on cannot be undone for an existing entity.

Each message carries a `SessionId`. The broker holds all messages with the same
session ID together and guarantees first-in-first-out delivery only within that
session; across sessions there is no ordering guarantee and no head-of-line
blocking. This is why sessions are used for ordered workflows rather than for
global ordering of a queue.

A receiver accepts a session, not an individual message. While the session is
locked, other receivers cannot accept it, which gives exclusive processing
without an external distributed lock. The lock has a timeout and must be renewed
when processing is long-running.

Session state lets a consumer persist a small amount of data between messages of
the same session, such as a running total or a last-processed sequence number.
The state is stored by the broker and retrieved with the session, so a restarted
consumer resumes where the previous one stopped.

_Hand-written sample fixture for smoke tests, not a copy of Microsoft
documentation._
