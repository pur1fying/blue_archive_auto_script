
# 💀 Bedienungsanleitung für das Hardship Map

Die **Hardship Map** funktioniert ähnlich wie die Modi **Team-Logik** und **Normale Graphen**.
Einige schwierige Karten erfordern **drei Teams**, die alle **das gleiche Attribut** wie das zuerst im Gebiet zugeordnete Team teilen.

---

## 🧾 Ausfüllanleitung

### ⚠️ Erlaubte Zeichen

Der **String**, den du für den Slide-Level eingibst, darf **nur** folgende Zeichen oder Wörter enthalten:

```
"-", "sss", "present", "task", ",", [Zahlen]
```

Jede Segmentgruppe soll durch Kommas (`,`) getrennt sein.

> ❌ Füge **nicht** irgendwelche Schlüsselwörter wie `"sss"`, `"present"` oder `"task"` außerhalb gültiger Syntax ein.

---

### 🧩 Beispiel 1: Grundlegende Nutzung

**Eingabe:**

```text
15,12-2
```

**Interpretation:**
BAAS führt die Aufrufe durch:

```text
15-1, 15-2, 15-3, 12-2
```

und agiert gemäß der Hard Map Einstellungen:

* `sss` → Sternebewertung
* `present` → Belohnung einholen
* `task` → Herausforderung durchführen

---

### 🧩 Beispiel 2: Zahl + Schlüsselwort

**Eingabe:**

```text
15-sss-present
```

**Bedeutung:**
BAAS führt die Levelgruppen **15-1, 15-2, 15-3** aus
und führt sowohl `sss` (Sternebewertung) als auch `present` (Geschenke einsammeln) aus.

---

### 🧩 Beispiel 3: Zwei Zahlen + Schlüsselwörter

**Eingabe:**

```text
15-3-sss-task
```

**Bedeutung:**
Dies ruft **Level 15-3** auf, um:

* die `sss` Bewertung zu erreichen
* die `task` Herausforderung abzuschließen

---

### 🧩 Beispiel 4: Komplexes Beispiel

**Eingabe:**

```
7,8-sss,9-3-task
```

**Bedeutung:**

* Ruft `(7-1, 7-2, 7-3)` auf → führe `sss`, Geschenke einsammeln und Herausforderungen aus
* Ruft `(8-1, 8-2, 8-3)` auf → führe `sss`
* Ruft `9-3` auf → absolviere die `task` Herausforderung

---

## 🧠 Systemverhalten

> 🟡 **Hinweis:**
> BAAS bestimmt automatisch, ob:
>
> * ein Level bereits **`sss`** erreicht hat, oder
> * ein **Geschenk / present** bereits eingesammelt wurde.

Falls eine dieser Bedingungen bereits erfüllt ist, **wird das Level automatisch übersprungen**, um Laufzeit zu optimieren.
