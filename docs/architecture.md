# Architecture

```text
text / SSMD -> document parser -> language plan -> linguistic pass A
    -> written-to-spoken preparation -> linguistic pass B
    -> segmentation -> directive resolution -> pause planning
    -> units and hashes -> .ttsplan.json -> renderer
```

The preparation boundary preserves both structural and spoken coordinate spaces. Linguistic analysis is request-local and provider documents are released before the immutable plan is returned. Pause events retain provenance and resolved event IDs; plan identity excludes diagnostics and producer metadata while unit hashes include ordered segment semantics, resolved pauses, and marker content.

TTSPlan ends before G2P and audio. Public plans contain only immutable, JSON-compatible semantic results. Live parser resources, provider documents, spaCy documents, models, and sessions are request-local. The plan file, rather than a Python object graph, is the inter-package contract.
