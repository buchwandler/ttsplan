# PyKokoro reference

The sibling `../pykokoro` checkout is a read-only migration oracle. Phase A production code never imports it. Reference tests, when enabled, run the sibling in a subprocess and compare normalized engine-neutral semantics only.

Repository: `../pykokoro`
Reference commit: `4df2043695e889d56fd4b0ddeb21f15f7c9f65f8`

Intentional boundary differences include resolving effective pauses before serialization and representing directives as typed semantic values instead of provider-specific G2P state. Differences caused by model selection, phonemes, token IDs, audio, and acoustic runtime are outside parity scope.
