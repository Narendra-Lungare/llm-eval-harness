# Dead-letter queues

The dead-letter queue (DLQ) is a secondary sub-queue that holds messages that
cannot be delivered or processed. Each queue and each subscription has its own
DLQ; it is not a separately created entity and cannot be deleted.

A message normally moves to the DLQ for one of these reasons:

- It exceeded the entity's `MaxDeliveryCount`, meaning the receiver asked for it
  more than the configured number of times without completing it.
- Its time-to-live expired while it was still in the queue for a queue entity.
- The receiver explicitly called dead-letter on the message, for example after
  validating that the payload is malformed.

When a message is dead-lettered, the broker appends the `DeadLetterReason` and
`DeadLetterErrorDescription` custom properties so the failure is diagnosable
without an external log. Dead-lettered messages retain their original body and
system properties, including `MessageId`, so a replay tool can deduplicate.

The DLQ is read the same way as the main entity, but it must be addressed
explicitly by the client. Messages in the DLQ are not delivered to normal
receivers and do not count toward the active message count of the entity.
Resubmitting a dead-lettered message means sending a new message with the same
body; the broker does not move it back automatically.

_Hand-written sample fixture for smoke tests, not a copy of Microsoft
documentation._
