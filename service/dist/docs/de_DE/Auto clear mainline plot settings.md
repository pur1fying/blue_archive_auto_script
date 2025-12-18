
# 🧩 Einstellungen für automatisches Freischalten der Hauptstory

### 🎮 Autoplay und Kampf-Hinweise

**Autoplay** kann dir helfen, automatisch durch das Raster zu navigieren.
Allerdings **können manche Kämpfe im Final-Episode nicht automatisch ausgeführt werden.**

---

### 📘 Episoden-Nummerierung

| Nummer | Episodenname   |
| :----: | :------------- |
|    1   | Episode I      |
|    2   | Episode II     |
|    3   | Episode III    |
|    4   | Episode IV     |
|    5   | Finale Episode |
|    6   | Episode V      |

---

### 🔢 Eingabeformat

Verwende ein Komma („,“) zur Trennung der Zahlen, die jeweils eine Episode repräsentieren, die freigeschaltet werden soll.

**Beispiel:**

```text
1,2,3
```

Das bedeutet, dass das Skript die Episoden **Episode I → Episode II → Episode III** in Reihenfolge durchführt.

---

### ⚙️ Standardkonfiguration

Wenn das Eingabefeld leer gelassen wird und du auf **„Run“** klickst, wird folgende Standardabfolge verwendet:

| Region | Standardepisoden |
| :----- | :--------------- |
| CN     | `1,2,3,4`        |
| Global | `1,2,3,4,5,4`    |
| JP     | `1,2,3,4,5,4,6`  |
