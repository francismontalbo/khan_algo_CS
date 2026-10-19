# KaTeX 0.19.0

Pinned prebuilt runtime, stylesheet and WOFF2 fonts from the official npm release:
https://registry.npmjs.org/katex/-/katex-0.19.0.tgz

Upstream: https://github.com/KaTeX/KaTeX/releases/tag/v0.19.0
API: https://katex.org/docs/api
License: MIT; the original license is in `LICENSE`.

`tools/sync_assets.py` embeds the runtime, license, styles and WOFF2 fonts into
the application pages. Equations therefore work without a CDN, including local
files and standalone comparison, lesson and glossary exports. The original
upstream stylesheet is kept intact here; the embedded copy uses WOFF2 data URLs.
