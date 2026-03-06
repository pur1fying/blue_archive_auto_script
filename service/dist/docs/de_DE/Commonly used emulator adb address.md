
# 🧠 Referenz für Emulator-Ports

### ⚙️ Allgemeiner Hinweis

**Für die Multi-Instanz von Stimulator** solltest du die Konfiguration selbst prüfen.

---

### 🎮 Einzelner Emulator-Port

| Emulator                  | Port(s)          |
| :------------------------ | :--------------- |
| **MuMu**                  | `7555`           |
| **BlueStacks / LDPlayer** | `5555`           |
| **NoxPlayer**             | `62001`, `59865` |
| **MuMu 12**               | `16384`          |
| **MEmuPlay**              | `21503`          |

> ⚠️ **Wenn du BlueStacks nutzt**, stelle sicher, dass
> **die ADB-Port-Debug-Funktion** in den Einstellungen aktiviert ist.

---

💡 *Tipp:* Diese Ports werden für ADB-Verbindungen zwischen PC und Emulator verwendet.
Solltest du Verbindungsprobleme haben, vergewissere dich, dass die **ADB-Debugging-Option** im Emulator aktiviert ist und kein anderer Emulator dieselbe Portnummer belegt.
