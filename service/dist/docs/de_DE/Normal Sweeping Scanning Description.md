
# 🧹 Konfigurationsanleitung für Sweeping

Jede **Sweep-Konfiguration** folgt dem allgemeinen Format:

```
Region - Task-Nummer - Sweep-Anzahl
```

---

## 🧩 Aufbau

| Komponente       | Beschreibung                          |
| :--------------- | :------------------------------------ |
| **Region**       | Identifikator der Karte oder Gebietes |
| **Task-Nummer**  | Level oder Stufe in dieser Region     |
| **Sweep-Anzahl** | Anzahl der Durchläufe für das Sweepen |

Jede Konfigurationsangabe sollte durch Kommas (`,`) getrennt sein.

---

## 🗺️ 1. Verfügbare Sweep-Levels

Alle Karten **nach Academy 1 und Academy 5** werden vom automatischen Sweepen unterstützt.

> 🟡 **Beispiel gültiger Sweep-Strings:**
>
> ```
> 12-1-3, 13-2-2, 14-4-1
> ```

---

## ⚙️ 2. Spezifische Besonderheit

Auf dem **Internationalen Server** kann das Feld für `Sweep-Anzahl` das Schlüsselwort **`max`** enthalten.

* BAAS entscheidet automatisch, ob das Level beendet werden kann, abhängig von:

    * aktueller **Ausdauer (AP)**
    * Level-Schwierigkeit und Abschlussstatus

---

### 🧮 Beispiel

Wenn genug Ausdauer vorhanden ist:

```
15-3, 20-3-max
```

**Bedeutung:**

* Sweepen von **15-3** → dreimal
* Dann Sweepen von **20-3** → mit **der gesamten verbleibenden Ausdauer** (`max`)

---

✅ *Tipp:* Nutze `max` nur, wenn du willst, dass BAAS selbständig alle verbleibende Ausdauer auf diesem Level einsetzt. Ansonsten gib explizite Sweep-Anzahlen für genaue Steuerung an.
