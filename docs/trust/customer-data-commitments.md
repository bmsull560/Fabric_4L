# Customer Data Commitments

## 1) Data Ownership

- Customer data submitted to Value Fabric remains the property of the customer.
- Value Fabric acts as a processor/service provider for customer data, except where explicitly
  documented otherwise in contract terms.
- Value Fabric does not sell customer data.

## 2) Data Usage Boundaries

- Customer data is processed solely to provide, secure, support, and improve contracted services.
- Access to customer data is role-based and limited by least-privilege principles.
- Any third-party processing is governed by contractual and security controls documented in the
  subprocessor register.

## 3) Data Portability

Upon request and subject to contract terms, Value Fabric provides customer data export in
commonly used machine-readable formats.

Default portability targets:

- **Metadata and transactional records:** JSON and/or CSV.
- **Knowledge graph exports:** Structured JSON or graph-compatible export format.
- **Audit-relevant records:** Time-bounded exports with integrity metadata where available.

Target timelines (unless legal or technical constraints apply):

- Acknowledgement of export request: within **2 business days**.
- Standard export fulfillment: within **10 business days**.
- Complex export fulfillment: mutually agreed plan and timeline.

## 4) Data Deletion and Retention

- Customers may request deletion of their data at termination or by validated request.
- Value Fabric will execute deletion in production systems within **30 days** of validated request,
  unless a longer period is required by law or contractual retention obligations.
- Backups are overwritten on standard retention cycles and are not restored except for disaster
  recovery or legal obligations.
- A deletion confirmation will be provided after completion.

## 5) Customer Responsibilities

- Verify requester authorization before submitting portability or deletion requests.
- Maintain copies of exported data required for business continuity.
- Define tenant-scoped identifiers required to satisfy data subject or tenant deletion requests.

## 6) Request Channels

- Security/privacy contact: `security@valuefabric.example`
- Support channel: Customer support portal (authenticated request)

## 7) Exceptions

Where legal hold, fraud prevention, security logging, or statutory obligations apply, deletion may
be delayed or scoped. Any exceptions are documented and communicated to the customer.
