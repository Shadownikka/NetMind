# NetMind for Windows

AI-powered network manager for Windows 11 — monitor, control, and throttle every device on your local network from a single desktop app.

## Requirements

- Windows 11 (64-bit)
- Administrator account
- [Npcap](https://npcap.com/) — installed automatically by the installer
- Docker Desktop — installed automatically (optional, for monitoring dashboards)
- [Ollama](https://ollama.com/) — installed automatically (optional, for AI features)

## Installation

1. Download `NetMind-Setup-Windows.exe`
2. Right-click → **Run as administrator** (UAC prompt is expected — the app needs admin rights to manage network traffic)
3. Follow the setup wizard

> **Antivirus notice:** NetMind intercepts network packets and performs ARP operations to manage your LAN — behaviour that antivirus software may flag. If your AV quarantines the installer or the app, add an exclusion for `C:\Program Files\NetMind` before running.

## Features

- Per-device bandwidth limiting and blocking
- Real-time device monitoring
- AI chat + AutoPilot (100% local via Ollama — no data leaves your machine)
- Cloud sync — view your network remotely from the web dashboard
- Remote commands — block or limit devices from anywhere
- Free tier: up to 5 controlled devices
- Paid tier: up to 20 devices + advanced features

## Uninstalling

Use **Add/Remove Programs** → NetMind, or run `NetMind-Uninstall.exe` from the install folder.

## Latest Release

https://github.com/Shadownikka/NetMind/releases/latest
