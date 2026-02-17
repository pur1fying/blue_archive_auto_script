
# ⚔️ Leitfaden zur Konfiguration der Activity-Sweep

Diese Anleitung erklärt, wie du korrekt **Activity-Sweep-Parameter** für die BAAS-Automatisierung einstellst.

---

## 🧾 Einzelne Quest sweepen

**Parameter:**
`Sweep Quest Number`

* Typ: **Ganzzahl**
* Bereich: `1` – *Maximale Schwierigkeit* in der aktuellen Aktivität.

**Parameter:**
`Anzahl der Sweeps`

1. **Ganzzahl** → exakte Anzahl der Durchführungen.
   z. B. `3` bedeutet drei Durchläufe.
2. **Dezimalzahl** → Prozentsatz der aktuellen AP (Aktionspunkte) verwendet.
   z. B. `0.5` bedeutet `AP × 0.5`.
3. **Bruch** → anteilige AP-Nutzung.
   z. B. `1/3` bedeutet `AP × (1/3)`.

---

## 🔁 Mehrere Quests sweepen

Um mehrere Quests nacheinander zu sweepen,
verwende Kommas (`,`) zur Trennung der Questnummern.

**Beispiel:**

```text
Sweep Quest: 9, 10, 11  
Anzahl der Sweeps: 0.5, 3, 1/3  
AP: 999
```

**Interpretation:**

| Quest  | Berechnung       | Ergebnis     |
| :----- | :--------------- | :----------- |
| **9**  | (999 × 0.5) / 20 | 25 Mal       |
| **10** | Fix 3 Mal        | 3 Durchläufe |
| **11** | (999 × 1/3) / 20 | 16 Mal (ca.) |

➡️ BAAS sweept diese Quests **in der Reihenfolge**: Quest 9 → Quest 10 → Quest 11.

---

✅ *Tipp:* Vergewissere dich, dass dein **AP-Wert** dem im Spiel verfügbaren Ausdauerwert entspricht, bevor du mehrere Sweeps ausführst.
