<div align="center">

<img src="docs/assets/logo.png" alt="BAAS logo" width="128">

# Blue Archive Auto Script

**Hands-free Blue Archive, on every server.**<br>
Dailies, events, the café, shops and stories, all done while you're away.

[![GitHub stars](https://img.shields.io/github/stars/pur1fying/blue_archive_auto_script?style=for-the-badge&logo=github&color=4aa8ff&labelColor=1b2a3a)](https://github.com/pur1fying/blue_archive_auto_script/stargazers)
[![Release](https://img.shields.io/github/v/release/pur1fying/blue_archive_auto_script?style=for-the-badge&color=4aa8ff&labelColor=1b2a3a&label=release)](https://github.com/pur1fying/blue_archive_auto_script/releases)
[![License](https://img.shields.io/github/license/pur1fying/blue_archive_auto_script?style=for-the-badge&color=4aa8ff&labelColor=1b2a3a)](LICENSE)

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-00599C?style=flat-square&logo=cplusplus&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-8A2BE2?style=flat-square)
![AtomGit stars](https://atomgit.com/m0_74686738/blue_archive_auto_script/star/badge.svg)

<kbd>**English**</kbd> <kbd>[简体中文](docs/README_zh.md)</kbd>

<kbd>[Download](#-get-started)</kbd> <kbd>[Features](#-features)</kbd> <kbd>[Docs](https://baas.kiramei.moe/docs/en/)</kbd> <kbd>[Wiki](https://baas.wiki/)</kbd> <kbd>[Report a bug](#-reporting-bugs)</kbd> <kbd>[Contribute](#-contributing)</kbd>

</div>

---

**BAAS** is an automation tool for Blue Archive that supports all regional servers. It runs on any 16:9 game screen (1280 × 720 recommended), and our goal is simple: automate every in-game task, from dailies to events.

<div align="center">
  <img src="https://baas.kiramei.moe/media/desktop/en/dark/details-home.webp" alt="BAAS Tauri home page with profiles and logs" width="92%">
</div>

## 🚀 Get started

<div align="center">

[![Download BAAS Tauri](https://img.shields.io/badge/Download-BAAS%20Tauri-4aa8ff?style=for-the-badge&logo=github&logoColor=white&labelColor=1b2a3a)](https://github.com/Kiramei/baas-tauri/releases/latest)
[![Install guide](https://img.shields.io/badge/Read-Install%20guide-4aa8ff?style=for-the-badge&logo=gitbook&logoColor=white&labelColor=1b2a3a)](https://baas.kiramei.moe/docs/en/guide/install/)

![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat-square)
![macOS](https://img.shields.io/badge/macOS-000000?style=flat-square&logo=apple&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black)
![Android](https://img.shields.io/badge/Android-3DDC84?style=flat-square&logo=android&logoColor=white)

<sub>Still on the legacy UI? &nbsp;<kbd>[Legacy releases](https://github.com/pur1fying/blue_archive_auto_script/releases)</kbd> <kbd>[Legacy install guide](https://baas.wiki/usage_doc/install/choose_platform.html)</kbd> <kbd>[Source of BAAS Tauri](https://github.com/Kiramei/baas-tauri)</kbd></sub>

</div>

> [!TIP]
> For Android setup, WebUI and other deployment options, see the [BAAS Tauri docs](https://baas.kiramei.moe/docs/en/).

<details>
<summary><b>🔄 Moving from the legacy UI</b></summary>
<br>

1. If your legacy desktop build supports migration, open it once to export your profiles and preferences.
2. Launch BAAS Tauri and choose to migrate when prompted during initial setup.

On Windows, macOS and Linux, BAAS Tauri can reuse your existing installation folder and carry over your profiles, language, theme and any available MirrorChyan settings.

</details>

<details>
<summary><b>🧩 Installing the legacy UI on Windows</b></summary>
<br>

1. Download the legacy launcher archive from [GitHub Releases](https://github.com/pur1fying/blue_archive_auto_script/releases) or a QQ group.
2. Extract it to a path **without Chinese characters** (a Qt limitation).
3. Double-click `BlueArchiveAutoScript.exe` and wait for it to install the runtime. The UI opens automatically when setup finishes.

To build your own package with PyInstaller, see [`deploy/installer`](deploy/installer). More guides are on the [BAAS wiki](https://baas.wiki/).

</details>

## 🖼️ BAAS Tauri and the legacy UI

<table>
<tr>
<th width="50%">✨ BAAS Tauri</th>
<th width="50%">🧩 Legacy UI</th>
</tr>
<tr><td colspan="2" align="center"><sub><b>Home and logs</b></sub></td></tr>
<tr>
<td><img src="https://baas.kiramei.moe/media/desktop/en/dark/details-home.webp" alt="BAAS Tauri home and logs"></td>
<td><img src="docs/assets/compare/legacy-home.png" alt="Legacy BAAS home and logs"></td>
</tr>
<tr><td colspan="2" align="center"><sub><b>Tasks and scheduling</b></sub></td></tr>
<tr>
<td><img src="https://baas.kiramei.moe/media/desktop/en/dark/scheduler-list.webp" alt="BAAS Tauri task list with switches and run times"></td>
<td><img src="docs/assets/compare/legacy-tasks.png" alt="Legacy BAAS task switches"></td>
</tr>
<tr><td colspan="2" align="center"><sub><b>Settings</b></sub></td></tr>
<tr>
<td><img src="https://baas.kiramei.moe/media/desktop/en/dark/settings-general.webp" alt="BAAS Tauri general settings"></td>
<td><img src="docs/assets/compare/legacy-settings.png" alt="Legacy BAAS general settings"></td>
</tr>
</table>

<details>
<summary><b>📋 Feature comparison</b></summary>
<br>

| | ✨ BAAS Tauri | 🧩 Legacy UI |
| --- | --- | --- |
| **Platforms** | Windows · macOS · Linux · Android | Windows; macOS and Linux from source |
| **Setup** | Download and install | Extract to a path without Chinese characters, then wait for the runtime to install (Windows); conda + pip (macOS / Linux) |
| **Scheduling** | Visual scheduler and workflow editor | Task list |
| **Device preview** | ✅ Live | — |
| **Logs** | ✅ | ✅ |
| **Updates** | ✅ In-app | ✅ Via launcher restart |
| **WebUI / Docker** | ✅ [Guide](https://baas.kiramei.moe/docs/en/guide/webui/) | — |
| **Android** | ✅ | — |

</details>

## 🎯 Features

| | Feature | What BAAS automates |
| :-: | --- | --- |
| 💗 | **Student affinity** | Pets students up to eight times a day in the café and prioritizes your chosen students in lessons. |
| 🗺️ | **Missions** | Clears Normal areas 4–30 and Hard areas 1–30, including Area 30. |
| ☕ | **Café** | Invites the student of your choice with a ticket, pets students and collects café rewards. |
| 🛒 | **Shops** | Buys what you pick and refreshes the regular and Tactical Challenge shops as many times as you set. |
| 🎁 | **Daily rewards** | Collects club AP, mail, Tactical Challenge rewards, daily mission rewards, and Pass points and rewards. |
| ⚡ | **AP spending** | Sweeps selected Normal and Hard missions, Special Commissions and event stages. |
| 📚 | **Lessons** | Prefers chosen students or higher-affinity lessons, with a run count per area. |
| ⚔️ | **Tactical Challenge** | Uses all challenge tickets and collects the daily reward. |
| 🔨 | **Crafting** | Runs all three crafting stages, with priorities, run counts and optional Booster Tickets. |
| 💬 | **MomoTalk** | Finishes pending conversations and relationship stories, then claims the Pyroxene. |
| 🎯 | **Joint Firing Drill** | Uses all tickets while a drill is active. |
| 📖 | **Stories** | Clears main, group and mini stories in one go. |
| 🎉 | **Events** | Clears event stories, missions, challenges and tile maps, kept up to date for three regional servers. |
| 🏆 | **Total Assault** | Ticket clearing and rewards are [currently disabled](module/total_assault.py#L9-L11). High-score auto-battle lives in [BAAS_Cpp](https://github.com/pur1fying/BAAS_Cpp) and is being integrated. |

> [!NOTE]
> BAAS works with any 16:9 emulator resolution, not just 1280 × 720. On slower hardware, lower the screenshot frequency and give tasks more time. Scheduling supports a fixed daily reset time and custom run intervals.

## ⚠️ Known issues

> [!WARNING]
> **Don't run BAAS while playing VALORANT.** You may receive a temporary suspension lasting several hours.

## 🐞 Reporting bugs

Please take five minutes to check and reproduce the problem before opening an [issue](https://github.com/pur1fying/blue_archive_auto_script/issues):

- [ ] Make sure BAAS is up to date. The legacy version updates itself when restarted from its launcher.
- [ ] Attach the UI log from the affected run.
- [ ] Attach an emulator screenshot or screen recording.

## 🤝 Contributing

We post open requests in [GitHub Issues](https://github.com/pur1fying/blue_archive_auto_script/issues) and the [developer guide](https://blog.lzwi.fun/blue_archive_auto_script/develop_doc/develop_guide). Pull requests are welcome, and we review every one carefully. Other ways to help:

- 🏷️ **Label data.** BAAS uses YOLOv8 to detect characters in auto-battle. Contact the maintainer to help label training data.
- 🌐 **Translate.** The legacy GUI ships in English, Simplified Chinese, Japanese and Korean.
- 📣 **Spread the word.** Stream automated high-score runs on Bilibili or make tutorials for your favorite video platform.

## 🧭 Roadmap

BAAS is a student-led open-source project. Come build it with us!

- [ ] Keep rewriting parts of BAAS in C++ in [BAAS_Cpp](https://github.com/pur1fying/BAAS_Cpp)
- [ ] An auto-battle UI that anyone can use
- [ ] More flexible AP planning during ×2 and ×3 drop campaigns, with stage choices and AP purchases
- [ ] Pyroxene farming for new Tactical Challenge seasons

## 💬 Community

| Channel | |
| --- | --- |
| QQ group 1 | `658302636` |
| QQ group 2 | `1027430247` |
| Developer contact | Email the maintainer, [pur1fying](mailto:2274916027@qq.com) |

## 💖 Acknowledgments

Thanks to everyone who has helped build BAAS. See the full [acknowledgments](https://baas.wiki/thanks) and [contributors](https://github.com/pur1fying/blue_archive_auto_script/graphs/contributors).

<p align="center">
  <a href="https://github.com/pur1fying/blue_archive_auto_script/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=pur1fying/blue_archive_auto_script&columns=21" alt="BAAS contributors" width="100%">
  </a>
</p>

---

<div align="center">
<sub>BAAS is released under the <a href="LICENSE">GNU General Public License v3.0</a>.</sub>
</div>
