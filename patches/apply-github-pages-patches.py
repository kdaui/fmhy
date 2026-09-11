#!/usr/bin/env python3
"""
Apply base-path patches for GitHub Pages deployment under /fmhy/.

Run from the repository root:
    python3 patches/apply-github-pages-patches.py

All changes are confined to files that VitePress reads at build time.
Upstream source is never modified in the main branch; this script runs
only inside CI before the build step.
"""

import re, pathlib, sys

BASE = "/fmhy/"
ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def replace_in_file(relpath: str, old: str, new: str) -> None:
    p = ROOT / relpath
    text = p.read_text(encoding="utf-8")
    if old not in text:
        print(f"  WARN: pattern not found in {relpath}, skipping")
        print(f"        looking for: {old!r}")
        return
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print(f"  OK   {relpath}")


# ---------------------------------------------------------------------------
# 1. docs/.vitepress/config.mts
# ---------------------------------------------------------------------------
print("[1/7] config.mts — base URL")
replace_in_file(
    "docs/.vitepress/config.mts",
    "const baseUrl = process.env.GITHUB_ACTIONS ? '/edit' : '/'",
    f"const baseUrl = '{BASE}'",
)

print("[2/7] config.mts — RSS head link")
replace_in_file(
    "docs/.vitepress/config.mts",
    "href: '/feed.rss'",
    f"href: '{BASE}feed.rss'",
)

print("  ++  config.mts — icon / manifest / touch-icon / logo paths")
replace_in_file(
    "docs/.vitepress/config.mts",
    "href: '/fmhy.ico'",
    f"href: '{BASE}fmhy.ico'",
)
replace_in_file(
    "docs/.vitepress/config.mts",
    "href: '/manifest.json'",
    f"href: '{BASE}manifest.json'",
)
replace_in_file(
    "docs/.vitepress/config.mts",
    "href: '/pwa_icon.png'",
    f"href: '{BASE}pwa_icon.png'",
)
replace_in_file(
    "docs/.vitepress/config.mts",
    "src: '/fmhy.ico'",
    f"src: '{BASE}fmhy.ico'",
)

print("[3/7] config.mts — transformHead call")
replace_in_file(
    "docs/.vitepress/config.mts",
    "transformHead: async (context) => generateMeta(context, meta.hostname),",
    "transformHead: async (context) => generateMeta(context, meta.hostname, baseUrl),",
)

# ---------------------------------------------------------------------------
# 2. docs/.vitepress/hooks/meta.ts
# ---------------------------------------------------------------------------
print("[4/7] meta.ts — add base param & fix URLs")
meta_ts = ROOT / "docs/.vitepress/hooks/meta.ts"
text = meta_ts.read_text(encoding="utf-8")

# a) function signature
text = text.replace(
    "export function generateMeta(context: TransformContext, hostname: string) {",
    "export function generateMeta(context: TransformContext, hostname: string, base: string = '') {",
)

# b) canonical / og:url line — replace the url construction
text = text.replace(
    "const url = `${hostname}/${pageData.relativePath.replace(/((^|\\/)index)?\\.md$/, '$2')}`",
    "const path = pageData.relativePath.replace(/((^|\\/)index)?\\.md$/, '$2')\n  const url = `${hostname}${base}${path}`",
)

# c) image meta tags — replace ${hostname}/ with ${hostname}${base}
text = text.replace(
    "content: `${hostname}/${pageData.frontmatter.image.replace(/^\\//, '')}`",
    "content: `${hostname}${base}${pageData.frontmatter.image.replace(/^\\//, '')}`",
)

# d) og:image / twitter:image for generated og images
text = text.replace(
    "content: `${hostname}/${imageUrl}`",
    "content: `${hostname}${base}${imageUrl}`",
)

meta_ts.write_text(text, encoding="utf-8")
print("  OK   hooks/meta.ts (multi-line)")

# ---------------------------------------------------------------------------
# 3. docs/.vitepress/hooks/rss.ts
# ---------------------------------------------------------------------------
print("[5/7] rss.ts — feed item URLs")
rss_ts = ROOT / "docs/.vitepress/hooks/rss.ts"
text = rss_ts.read_text(encoding="utf-8")

text = text.replace(
    "id: `${meta.hostname}${url.replace(/\\/\\d+\\./, '/')}`",
    "id: `${meta.hostname}${config.site.base}${url.replace(/\\/\\d+\\./, '/')}`",
)
text = text.replace(
    "link: `${meta.hostname}${url.replace(/\\/\\d+\\./, '/')}`",
    "link: `${meta.hostname}${config.site.base}${url.replace(/\\/\\d+\\./, '/')}`",
)

rss_ts.write_text(text, encoding="utf-8")
print("  OK   hooks/rss.ts")

# Fix feed favicon URL to include the base path
rss_fix = ROOT / "docs/.vitepress/hooks/rss.ts"
text = rss_fix.read_text(encoding="utf-8")
if "favicon: `${meta.hostname}/favicon.ico`" in text:
    text = text.replace(
        "favicon: `${meta.hostname}/favicon.ico`",
        f"favicon: `${{meta.hostname}}{BASE}favicon.ico`",
    )
    rss_fix.write_text(text, encoding="utf-8")
    print("  ++  hooks/rss.ts feed favicon")

# ---------------------------------------------------------------------------
# 4. docs/.vitepress/theme/Posts.vue
# ---------------------------------------------------------------------------
print("[6/7] Posts.vue — RSS link & post links")
posts_vue = ROOT / "docs/.vitepress/theme/Posts.vue"
text = posts_vue.read_text(encoding="utf-8")

text = text.replace(
    '<a href="/feed.rss" target="_blank" title="RSS feed">',
    f'<a href="{BASE}feed.rss" target="_blank" title="RSS feed">',
)
text = text.replace(
    ':href="post.url"',
    ':href="withBase(post.url)"',
)

posts_vue.write_text(text, encoding="utf-8")
print("  OK   theme/Posts.vue")

# ---------------------------------------------------------------------------
# 5. docs/.vitepress/shared.ts — feedback link
# ---------------------------------------------------------------------------
print("[7/7] shared.ts — feedback link")
shared_ts = ROOT / "docs/.vitepress/shared.ts"
text = shared_ts.read_text(encoding="utf-8")

text = text.replace(
    'href="/feedback"',
    f'href="{BASE}feedback"',
)

# Point canonical / OG / RSS / sitemap URLs at the deployed GitHub Pages site
text = text.replace(
    "hostname: 'https://fmhy.net'",
    "hostname: 'https://kdaui.github.io'",
)

shared_ts.write_text(text, encoding="utf-8")
print("  OK   shared.ts")

# ---------------------------------------------------------------------------
# 6b. docs/.vitepress/theme/index.ts — seasonal favicon paths
# ---------------------------------------------------------------------------
print("  BONUS theme/index.ts — seasonal favicon paths")
theme_index_ts = ROOT / "docs/.vitepress/theme/index.ts"
text = theme_index_ts.read_text(encoding="utf-8")

text = text.replace(
    "'/june_icon.webp'",
    f"'{BASE}june_icon.webp'",
)
text = text.replace(
    "'/fmhy.ico'",
    f"'{BASE}fmhy.ico'",
)

theme_index_ts.write_text(text, encoding="utf-8")
print("  OK   theme/index.ts")

# ---------------------------------------------------------------------------
# 6c. docs/.vitepress/theme/style.scss — June branding image
# ---------------------------------------------------------------------------
print("  BONUS theme/style.scss — June branding image")
style_scss = ROOT / "docs/.vitepress/theme/style.scss"
text = style_scss.read_text(encoding="utf-8")

text = text.replace(
    "url('/june_icon.webp')",
    f"url('{BASE}june_icon.webp')",
)

style_scss.write_text(text, encoding="utf-8")
print("  OK   theme/style.scss")

# ---------------------------------------------------------------------------
# 6. docs/public/manifest.json — PWA scope & start_url
# ---------------------------------------------------------------------------
print("  BONUS manifest.json — PWA scope & start_url")
manifest = ROOT / "docs/public/manifest.json"
text = manifest.read_text(encoding="utf-8")

text = text.replace('"scope": "/"', f'"scope": "{BASE}"')
text = text.replace('"start_url": "/"', f'"start_url": "{BASE}"')

manifest.write_text(text, encoding="utf-8")
print("  OK   public/manifest.json")

# ---------------------------------------------------------------------------
# 7. docs/index.md — hero announcement link
# ---------------------------------------------------------------------------
print("  BONUS index.md — hero announcement link")
index_md = ROOT / "docs/index.md"
text = index_md.read_text(encoding="utf-8")

# The announcement link changes over time (e.g. /posts/june-2026, /posts/sept-2026)
# Prefix any /posts/... link in the frontmatter hero announcement
text = re.sub(
    r'(link:\s+)/posts/',
    rf'\1{BASE}posts/',
    text,
)

# Fix hardcoded image paths in the uwu <script> block
text = text.replace("img.src = '/logo-uwu.svg'", f"img.src = '{BASE}logo-uwu.svg'")
text = text.replace("img.src = '/test.png'", f"img.src = '{BASE}test.png'")

index_md.write_text(text, encoding="utf-8")
print("  OK   index.md")

print("\nAll patches applied successfully.")
