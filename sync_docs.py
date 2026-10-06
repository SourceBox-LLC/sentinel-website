#!/usr/bin/env python3
"""
Sync documentation from Sentinel repos into the sentinel-website docs mirror.

Fetches READMEs, docs/ directories, and extra files from Sentinel-Command,
Sentinel-CameraNode, and Sentinel-HomeAssistant via the GitHub API, writes
them into docs/documentation/, rewrites their relative links so they work on
this site, and generates _sidebar.md.

Why links are rewritten: docsify resolves a relative link from the site root,
not from the page it is on. A link written as `docs/ARCHITECTURE.md` inside
`command/AGENTS.md` works on GitHub but goes to `/docs/ARCHITECTURE` here,
which does not exist. So every relative link becomes:
  - an absolute site link (`/command/docs/ARCHITECTURE.md`) when the target
    is a mirrored Markdown file (or a directory with a mirrored README);
  - a GitHub link when it isn't (source files, LICENSE, compose files);
  - a raw GitHub URL for images.
Links inside fenced code blocks are left alone.
"""
import base64
import json
import posixpath
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
MIRROR = ROOT / "docs" / "documentation"
ORG = "SourceBox-LLC"
BRANCH = "master"

REPOS = [
    {
        "slug": "command",
        "name": "Command Center",
        "github": "Sentinel-Command",
        "files": ["README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md"],
        "dirs": ["docs"],
        # Prompts for generated marketing images, not documentation.
        "exclude": ["docs/image-specs/README.md"],
    },
    {
        "slug": "camera-node",
        "name": "Camera Node",
        "github": "Sentinel-CameraNode",
        "files": ["README.md"],
        "dirs": ["docs"],
        "exclude": [],
    },
    {
        "slug": "home-assistant",
        "name": "Home Assistant",
        "github": "Sentinel-HomeAssistant",
        "files": ["README.md"],
        "dirs": [],
        "exclude": [],
    },
]

# The sidebar, grouped by what the reader came to do. Each entry is
# (site path without .md, title). A page that exists but isn't listed here
# lands under "More" rather than disappearing, so a new doc in a source repo
# still shows up before anyone edits this list.
SECTIONS = [
    ("Get started", [
        ("camera-node/README", "Install a CameraNode"),
        ("command/README", "Command Center"),
        ("home-assistant/README", "Home Assistant integration"),
        ("camera-node/docs/runbooks/local-mode-setup", "CameraNode without the cloud (local mode)"),
        ("camera-node/docs/runbooks/video-not-showing", "Troubleshooting: video not showing"),
    ]),
    ("How it works", [
        ("command/docs/ARCHITECTURE", "System architecture"),
        ("command/docs/SENTINEL_AGENT", "Sentinel AI agent"),
        ("command/SECURITY", "Security policy"),
    ]),
    ("Developer reference", [
        ("command/AGENTS", "Command Center internals"),
        ("command/docs/README", "Command Center docs index"),
        ("camera-node/docs/README", "CameraNode docs index"),
        ("command/CONTRIBUTING", "Contributing"),
        ("command/CODE_OF_CONDUCT", "Code of conduct"),
    ]),
    ("Operations", [
        ("command/docs/runbooks/ON_CALL", "On-call runbook"),
        ("command/docs/runbooks/DISASTER_RECOVERY", "Disaster recovery"),
        ("command/docs/LAUNCH_HANDOFF", "Launch checklist"),
    ]),
    ("Decision records", "adr"),       # every page under an adr/ directory
    ("Legal drafts", [
        ("command/docs/legal/DPA", "Data processing agreement (draft)"),
        ("command/docs/legal/SUB_PROCESSORS", "Sub-processors (draft)"),
    ]),
]


def gh_api(path):
    result = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return None


def download_file(repo, filepath, outpath):
    data = gh_api(f"repos/{ORG}/{repo}/contents/{filepath}")
    if not data or data.get("type") != "file":
        return False
    content = base64.b64decode(data["content"])
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_bytes(content)
    return True


def download_dir(repo, dirpath, outdir, exclude):
    contents = gh_api(f"repos/{ORG}/{repo}/contents/{dirpath}")
    if not isinstance(contents, list):
        return 0
    count = 0
    for item in contents:
        if item["type"] == "file" and item["name"].endswith(".md"):
            if item["path"] in exclude:
                continue
            if download_file(repo, item["path"], outdir / item["name"]):
                count += 1
        elif item["type"] == "dir":
            count += download_dir(repo, item["path"], outdir / item["name"], exclude)
    return count


# ── Link rewriting ───────────────────────────────────────────────────

MD_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)((?:\s+\"[^\"]*\")?)\)")
HTML_LINK = re.compile(r"""(\b(?:href|src)=")([^"]+)(")""")
FENCE = re.compile(r"^(```|~~~)")


def is_external(url):
    return url.startswith(("http://", "https://", "mailto:", "#", "/", "data:"))


def resolve(url, file_rel, repo, slug, mirrored, image):
    """The URL a relative link should have on this site."""
    path, _, frag = url.partition("#")
    target = posixpath.normpath(posixpath.join(posixpath.dirname(file_rel), path))
    if target.startswith(".."):
        return url  # points outside the repo; leave it
    anchor = f"#{frag}" if frag else ""
    if image:
        return f"https://raw.githubusercontent.com/{ORG}/{repo}/{BRANCH}/{target}"
    if target.endswith(".md") and target in mirrored:
        return f"/{slug}/{target}{anchor}"
    readme = "README.md" if target == "." else f"{target}/README.md"
    if readme in mirrored and (path.endswith("/") or "." not in posixpath.basename(target)):
        return f"/{slug}/{readme}{anchor}"
    looks_like_dir = path.endswith("/") or "." not in posixpath.basename(target)
    kind = "tree" if looks_like_dir and target not in ("LICENSE", "NOTICE", "Dockerfile") else "blob"
    where = "" if target == "." else f"/{target}"
    return f"https://github.com/{ORG}/{repo}/{kind}/{BRANCH}{where}{anchor}"


def rewrite_links(text, file_rel, repo, slug, mirrored):
    out, in_fence = [], False
    for line in text.split("\n"):
        if FENCE.match(line.lstrip()):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        def fix_md(m):
            bang, label, url, title = m.groups()
            if is_external(url):
                return m.group(0)
            return f"{bang}[{label}]({resolve(url, file_rel, repo, slug, mirrored, bool(bang))}{title})"

        def fix_html(m):
            attr, url, end = m.groups()
            if is_external(url):
                return m.group(0)
            image = attr.strip().startswith("src")
            return f"{attr}{resolve(url, file_rel, repo, slug, mirrored, image)}{end}"

        line = MD_LINK.sub(fix_md, line)
        line = HTML_LINK.sub(fix_html, line)
        out.append(line)
    return "\n".join(out)


def first_heading(md_path):
    for line in md_path.read_text(errors="ignore").splitlines():
        if line.startswith("# "):
            return re.sub(r"[`*]", "", line[2:]).strip()
    return md_path.stem.replace("_", " ").replace("-", " ").title()


# ── Landing page ─────────────────────────────────────────────────────

LANDING_PAGE = """# Sentinel documentation

Sentinel is a private security-camera system by SourceBox. A **CameraNode** runs on your own hardware, records locally, and streams live video outbound to **Command Center**, the dashboard you open in a browser. Your recordings never leave your CameraNode. The cloud holds a short live buffer in memory, plus the snapshots and short clips attached to incidents.

## Get started

1. **[Install a CameraNode](/camera-node/README.md)** on the computer your cameras are plugged into.
2. **Sign up** at [app.sentinel-command.com](https://app.sentinel-command.com/sign-up), add a node in **Settings**, and paste its key into the CameraNode setup.
3. Your cameras appear on the dashboard within a minute.

Video not showing? See **[Troubleshooting: video not showing](/camera-node/docs/runbooks/video-not-showing.md)**.

## The pieces

- **[Command Center](/command/README.md)**: the dashboard, API, live-video relay, MCP server and the Sentinel AI agent. Hosted by SourceBox, or run it yourself.
- **[CameraNode](/camera-node/README.md)**: the software that runs on your hardware, captures your cameras, detects motion and records locally.
- **[Home Assistant integration](/home-assistant/README.md)**: your Sentinel cameras inside Home Assistant.

## Going deeper

- **[System architecture](/command/docs/ARCHITECTURE.md)**: how the services fit together.
- **[Sentinel AI agent](/command/docs/SENTINEL_AGENT.md)**: how the AI investigation works and how to run it yourself.
- **[Security policy](/command/SECURITY.md)**: how to report a vulnerability.
- **[Command Center internals](/command/AGENTS.md)**: the developer reference.

---

*These pages are copied from the [Sentinel-Command](https://github.com/SourceBox-LLC/Sentinel-Command), [Sentinel-CameraNode](https://github.com/SourceBox-LLC/Sentinel-CameraNode) and [Sentinel-HomeAssistant](https://github.com/SourceBox-LLC/Sentinel-HomeAssistant) repositories every hour.*
"""


def write_landing_page():
    """Write the docsify landing page (README.md) at the mirror root.

    The sidebar's first link is [Home](README), which docsify resolves to
    docs/documentation/README.md. The wipe loop below would delete it, so we
    regenerate it every run — never treat it as hand-curated.
    """
    (MIRROR / "README.md").write_text(LANDING_PAGE)


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print(f"Sentinel docs sync — {datetime.now(timezone.utc).isoformat()}")

    # Preserve index.html, wipe everything else in the mirror dir
    if MIRROR.exists():
        for item in MIRROR.iterdir():
            if item.name != "index.html":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    else:
        MIRROR.mkdir(parents=True)

    # Write the docsify landing page *after* the wipe so it always exists.
    write_landing_page()

    total_files = 0
    pages = {}  # site path (no .md) -> title

    for repo in REPOS:
        slug = repo["slug"]
        print(f"\n=== {repo['name']} ===")
        repo_dir = MIRROR / slug
        repo_dir.mkdir(parents=True, exist_ok=True)

        for f in repo["files"]:
            if download_file(repo["github"], f, repo_dir / f):
                print(f"  + {f}")
                total_files += 1
        for d in repo["dirs"]:
            count = download_dir(repo["github"], d, repo_dir / d, repo["exclude"])
            if count:
                print(f"  + {d}/ ({count} files)")
                total_files += count

        mirrored = {str(p.relative_to(repo_dir)) for p in repo_dir.rglob("*.md")}
        for rel in sorted(mirrored):
            md = repo_dir / rel
            md.write_text(rewrite_links(md.read_text(errors="ignore"), rel, repo["github"], slug, mirrored))
            pages[f"{slug}/{rel[:-3]}"] = first_heading(md)

    # ── Sidebar ──
    lines = ["<!-- Auto-generated by sync_docs.py — do not edit manually -->", "", "- [Home](README)", ""]
    listed = set()
    for section, entries in SECTIONS:
        if entries == "adr":
            entries = [(p, t) for p, t in sorted(pages.items()) if "/adr/" in p]
        present = [(p, t) for p, t in entries if p in pages]
        if not present:
            continue
        lines.append(f"- **{section}**")
        for path, title in present:
            lines.append(f"  - [{title}]({path})")
            listed.add(path)
        lines.append("")
    extra = [(p, t) for p, t in sorted(pages.items()) if p not in listed]
    if extra:
        lines.append("- **More**")
        for path, title in extra:
            lines.append(f"  - [{title}]({path})")
        lines.append("")
    lines.append("- [Report a bug](https://github.com/SourceBox-LLC/Sentinel-Command/issues)")
    lines.append("- [Edit on GitHub](https://github.com/SourceBox-LLC/sentinel-website)")
    lines.append("")
    (MIRROR / "_sidebar.md").write_text("\n".join(lines))

    print(f"\nGenerated _sidebar.md ({len(lines)} lines)")
    print(f"Total docs synced: {total_files} markdown files")
    print("Sync complete!")


if __name__ == "__main__":
    main()
