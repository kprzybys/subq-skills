---
title: Data retention
description: How long SubQ stores prompts, completions, and conversation history.
---

Each organization has one data-retention policy. It sets how long SubQ keeps
your prompts, completions, and conversation history. Contact SubQ to change
it.

- **Retain indefinitely (default)** — kept until you delete it.
- **Delete after *N* days** — deleted after *N* days; a `previous_response_id` older than that returns `404`.
- **Zero data retention** — nothing is stored.

SubQ always records model, token counts, timing, and your
[`metadata`](/endpoints/chat-completions-api/#metadata) tags for billing and
support. That record never includes prompts or completions.

## Zero data retention

Requests are unaffected; nothing is stored afterward. To enable it for your
organization, [request zero data retention](https://share-na2.hsforms.com/1ikOZ84D1RACcMJlibb1z9w418zam)
using the email you sign in to SubQ with.

| Endpoint                                             | Behavior                                                                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [Chat Completions](/endpoints/chat-completions-api/) | Unaffected.                                                                                                         |
| [Responses](/endpoints/responses-api/)               | Works, but turns aren't saved. Send the full context in `input` on every request instead of `previous_response_id`. |
| [Conversations](/endpoints/conversations-api/)       | Unavailable (`403` `zero_data_retention`).                                                                          |
| [Decisions](/endpoints/decisions-api/)               | Unaffected.                                                                                                         |
| Inline PDFs (`file_data`)                            | Rejected (`400` `document_source_unsupported`). Upload the file and pass [`file_id`](/using-the-api/file-inputs/).  |

## Opting out per request

To keep a single request out of storage, send `store: false` on
[Chat Completions](/endpoints/chat-completions-api/#storage) or
[Responses](/endpoints/responses-api/#storage).
