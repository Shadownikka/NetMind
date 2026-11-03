<div align="center">

<img src="https://netmindapp.com/assets/apple-touch-icon.png" width="96" alt="NetMind logo" />

# NetMind

**See every device on your network. Limit, block and manage them from one desktop app.**

For cafés, small offices, shops and homes · Windows and Linux

[Website](https://netmindapp.com) · [Download](#download) · [Docs](https://netmindapp.com/docs.html) · [Pricing](https://netmindapp.com/pricing.html) · [Changelog](https://netmindapp.com/changelog.html) · [Support](https://netmindapp.com/support.html)

</div>

---

This repository hosts the **official NetMind installers and updates** (in [Releases](https://github.com/Shadownikka/NetMind/releases)) and the update manifests the app checks. NetMind is closed-source; the app's source code is not published here.

## Download

| System | Installer | Version |
|---|---|---|
| **Windows 11** (64-bit) | [NetMind-Setup-Windows.exe](https://github.com/Shadownikka/NetMind/releases/download/v2.1.2-windows/NetMind-Setup-Windows.exe) | v2.1.2 |
| **Linux** (64-bit: Ubuntu, Debian, Kali, Fedora, Arch and similar) | [NetMind-Setup](https://github.com/Shadownikka/NetMind/releases/latest/download/NetMind-Setup) | [latest](https://github.com/Shadownikka/NetMind/releases/latest) |

Once installed, the app updates itself. You don't need to come back here for new versions.

### Beta builds

Beta builds are marked **Pre-release** on the [Releases](https://github.com/Shadownikka/NetMind/releases) page. They are still being tested and are **not** offered as automatic updates. Install one only if you want to try new features early.

| Beta | What's new |
|---|---|
| [Linux v2.1.3 beta](https://github.com/Shadownikka/NetMind/releases/tag/v2.1.3-linux-beta) | Smarter AI Chat and Autopilot, real device names, renaming devices, router name import, a Free-plan install without the AI |
| [Windows v2.1.3.1 beta](https://github.com/Shadownikka/NetMind/releases/tag/v2.1.3.1-beta) | Real device names, renaming devices, router name import, a Free-plan install without the AI |

Linux releases include a `SHA256SUMS` file. Check your download with `sha256sum -c SHA256SUMS`.

> **Only download NetMind from this page or from [netmindapp.com](https://netmindapp.com/download.html).**

## Install

**Windows**
1. Download `NetMind-Setup-Windows.exe` and double-click it. Click **Yes** on the administrator prompt.
2. The wizard installs Npcap, Docker Desktop and the local AI, then adds NetMind to the Start menu and desktop.
3. Open NetMind and sign in with your [netmindapp.com](https://netmindapp.com) account.

**Linux**
1. Download `NetMind-Setup`. Right-click it → **Properties** → **Permissions** → allow executing as a program.
2. Double-click it and enter your password. The wizard installs the system packages, Docker and the local AI.
3. Open NetMind from the desktop icon and sign in with your [netmindapp.com](https://netmindapp.com) account.

You need a free NetMind account. [Create one here](https://netmindapp.com/signup.html).

## What it does

- **Every device, live:** download and upload speed per device, plus what it is doing (streaming, gaming, calls, browsing).
- **Limit, block, free:** cap a device's speed, cut it off, or give it full speed back with one click.
- **Web dashboard:** see your network and send limit/block commands from any browser, on desktop or mobile.
- **Alerts and reports:** new-device alerts, webhooks, weekly email summary.
- **Charts:** Grafana dashboards running on your own computer.
- **AI Chat** *(Paid)*: manage the network in plain language, e.g. *"slow down the TV to 2 Mbps"*.
- **Autopilot** *(Paid)*: describe your rules once and the AI applies them every 30 seconds, never touching devices you protect.

## Free and Paid

| | Free | Paid |
|---|---|---|
| Monitor every device | ✓ | ✓ |
| Devices limited or blocked at the same time | 5 | Unlimited |
| Web dashboard, alerts, webhooks, weekly summary | ✓ | ✓ |
| Bandwidth history | 7 days | 30 days |
| AI Chat, Autopilot, Reconfigure | n/a | ✓ |
| Daily email report, priority support | n/a | ✓ |

Prices and how to upgrade: [netmindapp.com/pricing](https://netmindapp.com/pricing.html).

## Privacy

- **The AI runs on your own computer** (Llama 3.1). Your chat messages and network data are not sent to an AI service.
- **From version 2.1.3 (in beta now), device names and models never leave your network.** The cloud dashboard only sees labels such as `Device-23`, with their speeds and status. Older versions also send device names to your dashboard.
- NetMind measures how much data each device uses. It does **not** read the content of anyone's traffic.

Full details: [Privacy Policy](https://netmindapp.com/privacy.html).

## System requirements

| | Free (without AI) | Paid (with AI) |
|---|---|---|
| System | Windows 11 64-bit, or 64-bit Linux | same |
| Memory | 4 GB RAM | 8 GB RAM recommended |
| Disk used | about 3 GB | about 13 GB |
| Rights | Administrator / root | same |
| Network | Same local network as the devices you manage | same |

- Install NetMind on **one computer per network**, one that stays on. It only manages the network while it is running.
- Networks that isolate their clients (most public guest Wi-Fi) are not supported.

## Antivirus

NetMind routes your network's traffic through your computer and needs administrator rights, which is behaviour antivirus software watches for. If your antivirus blocks or removes NetMind, restore it and add an exclusion for `C:\Program Files\NetMind` (Windows) or `/opt/netmind` (Linux). Step-by-step help: [netmindapp.com/download](https://netmindapp.com/download.html#antivirus).

## Uninstall

- **Windows:** Settings → Apps → Installed apps → NetMind → Uninstall.
- **Linux:** open **NetMind Uninstaller** from your applications menu.

## Legal

Only use NetMind on networks you own or are authorised to manage.

Use of NetMind is subject to the [Terms of Service](https://netmindapp.com/terms.html). See [LICENSE](LICENSE). Third-party components are listed in the license file.

© 2026 NetMind. All rights reserved.
