# Architecture

```text
text / SSMD -> document parser -> language plan -> linguistic pass A
    -> written-to-spoken preparation -> linguistic pass B
    -> segmentation -> directive resolution -> pause planning
    -> units and hashes -> .ttsplan.json -> renderer
```

TTSPlan ends before G2P and audio. Public plans contain only immutable, JSON-compatible semantic results. Live parser resources, provider documents, spaCy documents, models, and sessions are request-local. The plan file, rather than a Python object graph, is the inter-package contract.
