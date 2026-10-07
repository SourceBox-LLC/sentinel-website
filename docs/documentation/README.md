# Sentinel documentation

Sentinel is a private security-camera system by SourceBox. A **CameraNode** runs on your own hardware, records locally, and streams live video outbound to **Command Center**, the dashboard you open in a browser. Your recordings never leave your CameraNode. The cloud holds a short live buffer in memory, plus the snapshots and short clips attached to incidents.

## Get started

1. **Sign up** at [app.sentinel-command.com](https://app.sentinel-command.com/sign-up).
2. In **Settings → Camera Nodes**, click **Add Node** and run the install command it shows on the computer your cameras are plugged into.
3. Your cameras appear on the dashboard within about a minute.

Then read **[Using Sentinel](/command/docs/USER_GUIDE.md)**: watching and recording, alerts, incidents, Sentinel AI, your team and your data.

Video not showing? See **[Troubleshooting: video not showing](/camera-node/docs/runbooks/video-not-showing.md)**.

## The pieces

- **[Command Center](/command/README.md)**: the dashboard, API, live-video relay, MCP server and the Sentinel AI agent. Hosted by SourceBox, or run it yourself.
- **[CameraNode](/camera-node/README.md)**: the software that runs on your hardware, captures your cameras, detects motion and records locally.
- **[Home Assistant integration](/home-assistant/README.md)**: your Sentinel cameras inside Home Assistant.

## Going deeper

- **[System architecture](/command/docs/ARCHITECTURE.md)**: how the services fit together.
- **[Sentinel AI agent](/command/docs/SENTINEL_AGENT.md)**: how the AI investigation works and how to run it yourself.
- **[Security policy](/command/SECURITY.md)**: how to report a vulnerability.
- **[Terms of Service](https://sentinel-command.com/legal/terms)** and **[Privacy Policy](https://sentinel-command.com/legal/privacy)**.
- **[Command Center internals](/command/AGENTS.md)**: the developer reference.

---

*These pages are copied from the [Sentinel-Command](https://github.com/SourceBox-LLC/Sentinel-Command), [Sentinel-CameraNode](https://github.com/SourceBox-LLC/Sentinel-CameraNode) and [Sentinel-HomeAssistant](https://github.com/SourceBox-LLC/Sentinel-HomeAssistant) repositories every hour.*
