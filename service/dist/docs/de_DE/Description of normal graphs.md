
# 📊 Beschreibung normaler Graphen

---

## 🧩 1. Nutzungsbeschreibung

### (1) Freischaltung und Auto-Kampf Anforderung

Du **musst aktivieren**:

* 🟡 **Automatisch Runden beenden freischalten**
* 🟡 **Autofight**

> Das System erkennt und aktiviert diese Funktionen gegebenenfalls automatisch.

---

### (2) Unterstützte Level

Unterstützte Hauptstory-Normallevel:
🟡 **4 – 25**

---

### (3) Bewegungslogik

Wenn BAAS-Slides fixiert sind, werden alle Teambewegungen mit **einem einzigen Klick** ausgeführt.
Da die Anzahl der Teams in *Blue Archive* Slides variiert,
unterscheiden sich die **Nummerierungskoordinaten** und die **Bewegungsreihenfolge** je nach Teamzusammenstellung.

---

### (4) Hinweise zur automatischen Extrapolation

Bei Durchführung der **automatischen Extrapolation**
🟡 **musst du sicherstellen, dass Teams mit kleineren und größeren Nummern korrekt zugeordnet sind.**
(Falls unsicher: Überprüfe die Teamnummern, bevor du fortfährst.)

---

### (5) Einstellungen für normale Thumbnails

BAAS legt Konfigurationen fest basierend auf:

* 🟢 **< Einstellungen für normale Thumbnails >**
* 🟢 **Ausgewählte Gruppenattribute**
* 🟢 **♪ Team-Logik ♪**

Diese bestimmen die korrekte Konfiguration für jeden Slide.

> Die zuerst entsprechende Eigenschaft im Diagramm ist **[1]**, die zweite ist **[2]**.

---

## 🤖 2. Team-Logik

1. Priorisiere die Teamwahl basierend auf **Gegenbeziehungen (Restraint / Counter)**, und verringere schrittweise die Abhängigkeit vom Attributs-Matching für verbleibende Gegner.
2. Bei Teamwahl gilt:
   `4 – (Teamnummer) ≥ Anzahl der noch benötigten Teams`.
3. Wenn weder (1) noch (2) erfüllt wird, lockere nach und nach die Gegenbeziehungen zwischen [1] Partnern.
4. Wenn bereits einige Teams ausgewählt sind und `4 – max(ausgewählte Teams) ≥ verbleibende Teams`,
   fülle die restlichen mit **optional möglichen Nummern**.
5. Wenn keine der obigen Bedingungen zutrifft, wähle standardmäßig **Team 1, 2, 3**.

---

### 🧠 Beispiel

Wahlreihenfolge für **23 [Explosion, Crossing] Task Force**:

* Ein Team, eine Operation.
* Wenn *Explosion Team 3* nicht im obigen Ablauf gewählt wurde, wähle **4** als zweites.
* Wenn immer noch nicht verfügbar, wähle **12** als letztes Team.

---

## 🚀 3. Beschreibung von Normal-Push-Chart-Leveln

### (1) Gebiet Push-Verhalten

Wenn du auf
🟡 **„Could not close temporary folder: %s“** stößt,
stellt jede eingegebene Zahl ein **Gebiet dar, das gepusht werden soll**.
Das Programm prüft, ob jeder Level innerhalb dieses Gebiets neu gespielt werden muss,
abhängig davon, ob das aktuelle Level bereits eine `SSS` Bewertung erreicht hat.

**Beispiel:**

```text
15, 16, 14
```

Das bedeutet, dass das Programm die Gebiete **15 → 16 → 14** der Reihe nach durchläuft.

---

### (2) Erzwingungs-Treffer Konfiguration

Wenn 🟡 **Erzwinge Treffer auf jedem angegebenen Level** aktiviert ist:

* Gib eine einzelne Zahl ein → pushe ein ganzes Gebiet einmal.
* Gib `Nummer-Nummer` ein → wähle ein genaues Unterlevel.

**Beispiel:**

```text
15, 16-3
```

---

✅ *Tipp:* Verifiziere stets, dass Levelnummern und Teamzuordnungen mit deiner **BAAS-Konfiguration** übereinstimmen, bevor du automatisierte Skripte ausführst, um Fehlverhalten zu vermeiden.
