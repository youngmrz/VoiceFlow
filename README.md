# VoiceFlow

<p align="center">
  <img src="media/hero.png" alt="VoiceFlow Hero" width="100%">
</p>

# Own your Voice.

**Dictate freely with local AI. Zero latency. Zero data leaks. Zero cost.**

VoiceFlow brings the power of OpenAI's Whisper directly to your Windows machine. It runs entirely on your hardware, ensuring your voice data never leaves your device. Designed for privacy, speed, and reliability.

<p align="center">
  <a href="https://github.com/infiniV/VoiceFlow/releases/download/v1.1.1/VoiceFlowSetup-1.1.1.exe">
    <img src="https://img.shields.io/badge/Download_for_Windows-000000?style=for-the-badge&logo=windows&logoColor=white" alt="Download">
  </a>
  <a href="https://github.com/infiniV/VoiceFlow">
    <img src="https://img.shields.io/badge/View_Source-000000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
</p>

---

### Why Pay for Noise?

Cloud dictation services charge monthly fees for privacy-invasive APIs. VoiceFlow is essentially free, fully local, and yours forever.

<p align="center">
  <img src="media/comparison.png" alt="Comparison" width="100%">
</p>

| Feature | VoiceFlow | Cloud Services |
| :--- | :---: | :---: |
| **Cost** | **$0.00** | $10-15/mo |
| **Data Privacy** | **100% Local** | Cloud Processed |
| **Offline Support** | **Full Capability** | None |
| **Latency** | **Real-time (Local)** | Network Dependent |
| **RAM Usage** | **~200-300MB** | ~800MB+ |
| **Account Required** | **No** | Yes |
| **Screen Data Collection** | **None** | Often Required |

---

### Unbreakable Privacy

Everything runs on localhost. Your microphone data never leaves your RAM. We physically can't sell your data because we never see it.

*   **Air-Gapped Safe**: Works completely offline.
*   **Open Source**: Verify the code yourself. Visualized via `View Source`.
*   **No Logs**: Processed in RAM, then discarded.

---

### Usage Flow

See exactly what VoiceFlow does at every step. No hidden processes, no cloud uploads. Just transparent, local AI.

<p align="center">
  <img src="media/how-it-works.png" alt="How It Works" width="100%">
</p>

#### 1. Ready
VoiceFlow waits silently in the background. A minimal indicator shows it's ready.

#### 2. Listening
Hold **`Ctrl+Win`** to speak naturally. Audio stays in RAM only. The interface visualizes your voice amplitude in real-time.

#### 3. Transcribe & Paste
Release the keys. Local AI processes audio, then auto-pastes text directly at your cursor.

<p align="center">
  <img src="media/app-dash.png" alt="VoiceFlow Dashboard" width="100%">
</p>

---

### Commercial Power. Zero Tags.

#### Neural Engine
*   **Tiny / Base** (~75MB): Instant speed for quick commands.
*   **Small / Medium** (~500MB): Balanced accuracy for general dictation.
*   **Large-v3** (~3GB): Maximum precision for long-form content.

#### Features
*   **Global Hotkey**: `Ctrl+Win` to dictate anywhere.
*   **99+ Languages**: Auto-detection built-in.
*   **Local History**: Searchable SQLite database of your transcriptions.
*   **Auto-Paste**: Types directly into your active window.

---

### Ready to go local?

Join thousands of users who have taken back control of their voice data. Open source and forever free.

<p align="center">
  <a href="https://github.com/infiniV/VoiceFlow/releases/download/v1.1.1/VoiceFlowSetup-1.1.1.exe">
    <img src="media/footer.png" alt="Download Now" width="100%">
  </a>
</p>

### [Download Installer v1.1.1 (Windows)](https://github.com/infiniV/VoiceFlow/releases/download/v1.1.1/VoiceFlowSetup-1.1.1.exe)

*Windows 10/11 • 64-bit • ~150MB*

<br>
<br>

---

# For Developers

Complete documentation for building and contributing to the VoiceFlow project.

### Repository Setup

Clone the repository and install dependencies to initialize the development environment.

```powershell
# Clone the repository
git clone https://github.com/infiniV/VoiceFlow.git
cd VoiceFlow

# Install dependencies (Frontend + Backend)
pnpm run setup
```

### Running Locally

Start the development server with hot-reload enabled.

```powershell
pnpm run dev
```

### Architecture Overview

*   **Core**: Pyloid (PySide6 + QtWebEngine)
*   **Inference**: faster-whisper (Optimized)
*   **Frontend**: React 18, Vite, Tailwind CSS
*   **UI System**: Shadcn, Lucide React

### Building Distribution

To create the standalone executable and installer locally:

```powershell
# Build application and installer
pnpm run build
```

[Releases](https://github.com/infiniV/VoiceFlow/releases) • [Issues](https://github.com/infiniV/VoiceFlow/issues) • [License](LICENSE)
