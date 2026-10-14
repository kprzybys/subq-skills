---
title: Models
description: Supported SubQ model IDs and what each one accepts.
---

Pass the model ID in the `model` field. IDs are case-sensitive. To list the IDs
available to your API key, use the [Models API](/endpoints/models-api/).

## SubQ Snap Preview

Use this model to generate fast, structured decisions.

- Model ID: `subq-snap-preview`
- Status: Public preview
- Endpoint: [Decisions](/endpoints/decisions-api/)
- Modalities: Text (input and output), Image (input only)
- Features: [Images](/endpoints/decisions-api/#images)
- Pricing: Input ($0.05 / 1M tokens), Output (Free)

## SubQ Preview

Use this model for long-context chat.

- Model ID: `subq-preview`
- Status: Early access
- Endpoint: [Chat Completions](/endpoints/chat-completions-api/), [Responses](/endpoints/responses-api/)
- Modalities: Text (input and output)
- Features: [Files](/using-the-api/file-inputs/), [Function calling](/using-the-api/function-calling/)
