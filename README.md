<div align="center">

<img src="assets/netmind.png" width="120" alt="NetMind Logo" />

# NetMind

### AI-Powered Network Manager for Linux

**See every device. Control every connection. Let AI do the thinking.**

[![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://kernel.org)
[![AI](https://img.shields.io/badge/AI-Llama%203.1%20%28100%25%20Local%29-FF6B35?style=for-the-badge&logo=meta&logoColor=white)](https://ollama.com)
[![Docker](https://img.shields.io/badge/Grafana-Prometheus-E6522C?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![Windows](https://img.shields.io/badge/Windows-Under%20Construction-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#-windows)

[**Features**](#-features) · [**Download**](#-download--install) · [**Using the App**](#-using-the-app) · [**Grafana**](#-grafana-dashboard) · [**FAQ**](#-faq)

---

> **NetMind is a standalone desktop application** for Linux that gives you complete visibility and control over every device on your home or office network — powered by a local AI that runs entirely on your machine. No cloud. No subscriptions. No data leaves your network.

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

**🔍 Real-Time Device Discovery**
Automatically detects every connected device. Re-scans every 30 seconds for new arrivals. Shows IP, name, and live speed per device.

**📊 Live Bandwidth Monitoring**
Per-device download and upload speeds updated every 3 seconds. Network-wide totals always visible.

**🕵️ Activity Recognition**
Identifies what each device is doing: YouTube, Netflix, Spotify, gaming, video calls, browsing — automatically.

**⚡ Instant Bandwidth Control**
- **Limit** — set a custom speed cap
- **Block** — cut off internet access instantly
- **Free** — restore full speed in one click

</td>
<td width="50%">

**🤖 AI AutoPilot**
Describe your goals once in plain English. AutoPilot applies smart policies every 30 seconds and logs every decision with its reasoning.

**💬 AI Chat Assistant**
Talk to your network in natural language. *"Which device is using the most bandwidth?"* → AI answers and can take action.

**📈 Grafana Dashboard**
Beautiful real-time graphs. Auto-provisioned, zero configuration. Access from any browser on your network.

**🔒 Trusted Devices**
Mark any device as trusted — it gets excluded from monitoring and control permanently, passing at full speed.

</td>
</tr>
</table>

> ⚠️ **Legal Notice** — NetMind should only be used on networks you own or have explicit written permission to manage.

---

## ⬇️ Download & Install

### Step 1 — Download

Go to the [**Releases**](../../releases/latest) page and download `NetMind-Setup`.

### Step 2 — Run the installer *(one time only)*

Open a terminal in the folder where you downloaded the file and run:

```bash
sudo -E ./NetMind-Setup
```

The setup wizard opens and handles everything automatically:

| Step | What happens |
|------|-------------|
| 1 | Detects your Linux distribution |
| 2 | Installs all system packages |
| 3 | Installs Python dependencies |
| 4 | Installs Docker + Docker Compose |
| 5 | Installs Ollama (local AI runtime) |
| 6 | Downloads the Llama 3.1 AI model (~4.9 GB) |
| 7 | Installs the NetMind application |
| 8 | Creates desktop icon and app menu entry |
| 9 | Health check |

### Step 3 — Double-click to launch *(from now on, always)*

After installation, **NetMind appears on your Desktop**. Just double-click it — no terminal needed ever again.

---

## 🖱️ Using the App

### First Launch — Onboarding

The first time you open NetMind, the **AI Onboarding Wizard** asks you to describe your network goals in plain English:

> *"I run a coffee shop. Give customers fast WiFi. My office PC gets priority. Limit any single device to 20 Mbps."*

> *"Fair sharing at home. No one should hog the bandwidth. Gaming consoles limited to 10 Mbps after 10pm."*

The AI generates a complete bandwidth policy from your description. Review it, then confirm.

---

### Dashboard Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🧠 NetMind  ●System  ●Monitor  ●AutoPilot   [Init] [▶Start] [■Stop] [📊]│
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  6       │  24.3    │  3.1     │  2       │  1       │  47             │
│ Devices  │ ↓ MB/s   │ ↑ MB/s   │ Limited  │ Blocked  │ AI Cycles       │
├─────────────────────────────────────────────────────────────────────────┤
│ 🤖 AutoPilot  ● Running · Decisions: 47 · Interval: 30s · Last: 12s ago │
├─────────────────────────────────────────────────────────────────────────┤
│ 📡 Connected Devices                                          [⟳ Scan]  │
│ ┌────────────────┬───────┬──────┬───────────┬──────────────┬──────┬───┐ │
│ │ IP / Name      │↓ KB/s │↑KB/s │  Status   │   Activity   │Action│Trs│ │
│ ├────────────────┼───────┼──────┼───────────┼──────────────┼──────┼───┤ │
│ │ 192.168.1.45   │ 9,234 │  182 │ 🟢 Active │ YouTube 4K   │L B F │Trs│ │
│ │ Device-23      │ 2,100 │  400 │ 🔴 Limited│ Video Call   │L B F │Trs│ │
│ │ 192.168.1.12   │     0 │    0 │ ⚪ Idle   │     —        │L B F │Trs│ │
│ │ 192.168.1.67   │   340 │   55 │ 🔒 Trusted│ Browsing     │  —   │Utr│ │
│ └────────────────┴───────┴──────┴───────────┴──────────────┴──────┴───┘ │
├─────────────────────────────┬───────────────────────────────────────────┤
│ 📋 AI Decision Log          │ 💬 AI Chat Assistant                      │
│ 16:45:03 [limit_device]     │ You: Which device uses the most bandwidth?│
│ 192.168.1.45 at 9,234 KB/s  │                                           │
│ → applying 5,000 KB/s limit │ AI: 192.168.1.45 — downloading at        │
│                             │ 9,234 KB/s. Currently streaming YouTube.  │
│ 16:45:33 [no_action]        │                                           │
│ All devices within bounds   │ You: Limit it to 3 Mbps.                  │
│                             │ AI: Done. Limit applied.                  │
└─────────────────────────────┴───────────────────────────────────────────┘
```

### Status Indicators

| Pill | What it means |
|------|--------------|
| ● **System** (green) | Network engine initialized, devices discovered |
| ● **Monitor** (green) | Actively measuring traffic for all devices |
| ● **AutoPilot** (amber) | AI is running and making autonomous decisions |

### Device Actions

| Button | Effect |
|--------|--------|
| **Limit** | Set a custom speed cap (e.g. 2,048 KB/s down / 512 KB/s up) |
| **Block** | Immediately cut off all internet access |
| **Free** | Remove any limit or block — restore full speed |
| **Trust** | Exclude device from all monitoring and control forever |

---

## 📈 Grafana Dashboard

After clicking **▶ Start**, real-time metrics flow automatically to Grafana:

**→ http://localhost:3000** &nbsp; Login: `admin` / `admin`

| Panel | Shows |
|-------|-------|
| Active / Limited / Blocked | Live device counts |
| Total Network Bandwidth | Real-time download + upload combined |
| Device Download Bandwidth | Per-device speed graph over time |
| Device Upload Bandwidth | Per-device upload over time |

Dashboard auto-refreshes every **5 seconds**.

---

## 💻 System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Linux — Ubuntu 20.04+, Debian 11+, Kali, Fedora 35+, Arch, Mint |
| **Privileges** | `sudo` / root required |
| **RAM** | 6 GB minimum (Llama 3.1 uses ~4 GB) |
| **Disk** | ~8 GB free (AI model: ~4.9 GB) |
| **Network** | Same LAN as devices you want to manage |
| **Internet** | Required during installation only |

---

## 🔧 Troubleshooting

### Ollama not reachable / AI errors

```bash
curl http://localhost:11434/api/tags    # check if running
ollama serve                            # start if not running
ollama list                             # confirm llama3.1 is present
ollama pull llama3.1                    # download if missing
```

### No devices appearing after Initialize

- Confirm you're on the same Wi-Fi or Ethernet as the target devices
- Click **⟳ Scan** for an immediate re-scan
- Check firewall: `sudo ufw status` (disable temporarily to test)

### Bandwidth readings show zero

- The device may be idle — open a website on it to generate traffic
- Wait 5–10 seconds after clicking ▶ Start for the first reading

### Grafana shows "No data"

1. Confirm monitoring is active (Monitor pill is **green**)
2. Check: **http://localhost:9091/targets** → should show **UP**
3. The target turns UP only after you click **▶ Start**

### Devices lost internet after app closed unexpectedly

Always click **■ Stop** before closing the app. If devices lost internet:

```bash
sudo bash /opt/netmind/stop.sh
```

---

## 🪟 Windows

> **🚧 Windows version is currently under construction.**
>
> We are actively working on a native Windows installer. Stay tuned — watch this repo for updates.

---

## ❓ FAQ

**Q: Does my data go anywhere?**
No. Everything runs on your machine. The AI is local (Ollama). No telemetry, no cloud sync, no data leaves your network.

**Q: Will devices notice anything is different?**
No. Their internet continues normally. NetMind is invisible to regular users and devices.

**Q: Does it work with HTTPS / encrypted traffic?**
Yes — NetMind only measures data volume, never content. All encrypted traffic passes through untouched.

**Q: Can I run it on a Raspberry Pi?**
The monitoring and control features work fine. The Llama 3.1 AI model needs ~4 GB RAM — most Pi models can't run it.

**Q: What happens if I close the app without clicking Stop?**
Devices may briefly lose internet for 1–2 minutes until their ARP caches expire. Always use **■ Stop**.

**Q: Can NetMind monitor devices on a different VLAN or subnet?**
No. NetMind only manages devices on the same local network segment as your machine.

---

## 🔬 How It Works

When you click **▶ Start**, NetMind positions itself as an invisible intermediary using **ARP spoofing** — it tells each device that it is the router, and tells the router about each device. All traffic flows through your machine, giving NetMind full visibility and control without intercepting content.

```
Your Devices ──────► NetMind (ARP man-in-middle) ──────► Router ──────► Internet
                          │
                          ├── Traffic Monitor   (per-device byte counters)
                          ├── Bandwidth Control (TC/HTB kernel shaping)
                          ├── Metrics Exporter  → Prometheus → Grafana
                          └── AutoPilot         (Llama 3.1 via Ollama)
```

---

## 📄 License

Copyright © 2026 NetMind. All rights reserved.

Licensed under the [MIT License](LICENSE).

---

<div align="center">

Built with ❤️ using **Python**, **PyQt6**, **Llama 3.1**, **Prometheus**, and **Grafana**

*Runs 100% on your hardware. No cloud required.*

</div>
