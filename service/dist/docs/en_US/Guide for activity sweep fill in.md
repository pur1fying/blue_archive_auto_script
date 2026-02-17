# ⚔️ Activity Sweep Fill-In Guide

This guide explains how to correctly configure **activity sweep parameters** for BAAS automation.

---

## 🧾 Sweep One Quest

**Parameter:**  
`Sweep Quest Number`

- Type: **Integer**
- Range: `1` – *maximum difficulty* in the current activity.

**Parameter:**  
`Number of Sweeps`

1. **Integer** → Represents *exact sweep times*.  
   e.g. `3` means perform the quest 3 times.  
2. **Decimal** → Represents a *percentage of current AP* (Action Points) used.  
   e.g. `0.5` means use **AP × 0.5** for sweeping.  
3. **Fraction** → Represents a *fractional AP usage*.  
   e.g. `1/3` means use **AP × (1/3)** for sweeping.

---

## 🔁 Sweep Multiple Quests

To sweep multiple quests sequentially,  
use commas (`,`) to separate quest numbers.

**Example:**
```

Sweep Quest: 9, 10, 11
Number of Sweeps: 0.5, 3, 1/3
AP: 999

```

**Interpretation:**

| Quest  | Calculation      | Result   |
|:-------|:-----------------|:---------|
| **9**  | (999 × 0.5) / 20 | 25 times |
| **10** | Fixed 3 times    | 3 times  |
| **11** | (999 × 1/3) / 20 | 16 times |

➡️ BAAS will sweep these quests **in order**: Quest 9 → Quest 10 → Quest 11.

---

✅ *Tip:* Always verify that your **AP value** corresponds to the in-game available stamina before executing multiple sweeps.
