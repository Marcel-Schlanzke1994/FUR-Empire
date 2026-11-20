# Third-party notices

## FUR staging tools

| Component | Version/source | License | Scope |
|---|---|---|---|
| Mailpit | `axllent/mailpit:v1.32.0` ([source](https://github.com/axllent/mailpit)) | MIT ([license](https://github.com/axllent/mailpit/blob/v1.32.0/LICENSE)) | Optional private staging mail catcher only; no production mail relay or FUR game runtime dependency. |

The production and local FUR game do not bundle Mailpit. Python and Node dependency manifests are audited and CI emits CycloneDX SBOMs; a complete transitive license manifest and image-level SBOM remain open work.

## Optional browser push runtime

| Component | Version | License | Scope |
|---|---:|---|---|
| pywebpush | 2.5.0 | MPL-2.0 | Optional Web Push encryption and VAPID sender; disabled until all VAPID settings are explicitly provided. |
| py-vapid | 1.9.6 | MPL-2.0 | VAPID key and JWT support. |
| http-ece | 1.2.1 | MIT | Web Push payload encryption support. |
| aiohttp | 3.14.5 | Apache-2.0 AND MIT | pywebpush transport dependency. |
| requests | 2.34.2 | Apache-2.0 | pywebpush synchronous sender transport. |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause | Public-key and payload cryptography. |

The exact transitive runtime versions are pinned in `requirements.lock`. This table lists the direct Web Push path; the dependency SBOM contains the remaining transitive packages and their metadata.


## Originale Warenicons 2026-11-09

Zehn eigenständig gezeichnete SVGs in `static/assets/goods/`; keine Drittanbieterquelle, keine neuen Lizenz- oder Paketimporte. Metadaten/Produktionsprompts: `assets/ASSET_MANIFEST.json`; Herkunft: `LICENSE_PROVENANCE.md`.
