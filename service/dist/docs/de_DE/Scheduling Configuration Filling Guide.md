
# 🕒 Leitfaden für Zeitplan-Konfigurationsfelder

Diese Anleitung beschreibt, wie du Zeitplan-Konfigurationsfelder korrekt ausfüllst und interpretierst, um automatisierte Aufgaben auszuführen.

---

## ⚙️ 1. Priorität

Wenn mehrere Aufgaben in der Warteschlange sind:

* Aufgaben mit **niedrigeren Prioritätswerten** werden **zuerst** ausgeführt.

> Beispiel:
> Aufgabe A (Priorität 1) läuft vor Aufgabe B (Priorität 2).

---

## ⏳ 2. Ausführungsintervall

* **Ganzzahl `0`** bedeutet, dass die Aufgabe **jeden Tag** (Intervall von einem Tag) wiederholt wird.
* Größere Ganzzahlen stehen für längere Intervalle zwischen den Ausführungen (in Tagen).

---

## 🕐 3. Täglicher Reset

Aufgaben werden täglich zu festen Zeiten automatisch ausgeführt. Das lässt sich in der **Neuen UI** einfach einstellen.

* **Format:**

```
[ [ h, m, s ] ]
```

*(UTC Zeit)*

* **Mehrere Zeitpunkte** können angegeben werden, getrennt durch Kommas.

**Beispiel:**

```
[ [ 0, 0, 0 ], [ 20, 0, 0 ] ]
```

**Bedeutung:**
Läuft um **0:00 UTC** und **20:00 UTC** (entspricht 8 Uhr und 4 Uhr Pekinger Zeit bei UTC+8).

---

## 🚫 4. Deaktivierte Zeitbereiche

Aufgaben **werden nicht ausgeführt** während festgelegter deaktivierter Zeitfenster. Das lässt sich ebenfalls in der **Neuen UI** einstellen.

* **Format:**

```
[ [ [ h1, m1, s1 ], [ h2, m2, s2 ] ] ]
```

*(UTC Zeit)*

* **Mehrere Intervalle** möglich, separat durch Kommas.

**Beispiel:**

```
[ [ [ 0, 0, 0 ], [ 24, 0, 0 ] ] ]
```

**Bedeutung:**
Aufgaben sind für den ganzen Tag deaktiviert.

---

## 🔁 5. Vor- und Nachaufgaben

Du kannst zusammenhängende Operationen verketten:

* **Pre-Tasks:** ausgeführt **vor** der aktuellen Aufgabe
* **Post-Tasks:** ausgeführt **nach** der aktuellen Aufgabe

> Dies stellt sicher, dass abhängige Aktionen in der richtigen Reihenfolge ausgeführt werden.
