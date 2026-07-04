# Sentinel Documentation

Documentation for the Sentinel platform — a private security camera system by SourceBox.

## Components

- **[Command Center](#/command/README)** — Cloud-hosted web dashboard for viewing cameras, managing organizations, and controlling access. Hosted on Fly.io with FastAPI + React 19.
- **[Camera Node](#/camera-node/README)** — On-premises software that runs on your hardware, connects USB cameras, performs local motion detection, and uploads encrypted HLS segments.
- **[Home Assistant](#/home-assistant/README)** — Home Assistant integration component for Sentinel.

## Architecture

Sentinel has two components with zero inbound ports:

- **Camera Node** (your premises) → outbound HTTPS → **Command Center** (our cloud) → outbound HTTPS → **Browser** (any device)

Recordings never leave your Camera Node. The cloud holds only a rolling 60-second in-memory HLS buffer.

## Key Docs

- [Architecture Diagrams & ADRs](#/command/docs/adr/0001-sync-schema-vs-alembic)
- [On-Call Guide](#/command/docs/runbooks/ON_CALL)
- [Disaster Recovery](#/command/docs/runbooks/DISASTER_RECOVERY)
- [Security Policy](#/command/SECURITY)
- [Camera Node Setup](#/camera-node/docs/runbooks/local-mode-setup)
- [Troubleshooting: Video Not Showing](#/camera-node/docs/runbooks/video-not-showing)

---

*This documentation is auto-synced from the [Sentinel-Command](https://github.com/SourceBox-LLC/Sentinel-Command), [Sentinel-CameraNode](https://github.com/SourceBox-LLC/Sentinel-CameraNode), and [Sentinel-HomeAssistant](https://github.com/SourceBox-LLC/Sentinel-HomeAssistant) repositories every hour.*
