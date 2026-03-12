# 🧹 Sweep Configuration Guide

Each **sweep configuration** follows the general format:

```
region - task-number - sweep-times
```

---

## 🧩 Structure

| Component       | Description                               |
|:----------------|:------------------------------------------|
| **Region**      | The map or area identifier.               |
| **Task Number** | The level or stage within that region.    |
| **Sweep Times** | The number of times to perform the sweep. |

Each configuration should be **separated by commas (`,`)**.

---

## 🗺️ 1. Available Sweep Levels

All maps **after Academy 1 and Academy 5** are supported for automated sweeping.

> 🟡 **Example of valid sweep strings:**
> ```
> 12-1-3, 13-2-2, 14-4-1
> ```

---

## ⚙️ 2. Special Description

On the **International Server**,  
the field for `sweep times` can take the keyword **`max`**.

- BAAS automatically determines whether the level can be cleared,  
  depending on:
  - current **stamina (AP)**  
  - level difficulty and completion status  

---

### 🧮 Example

When stamina is sufficient:

```
15-3, 20-3-max
```

**Meaning:**

- Sweep **15-3** three times.  
- Then sweep **20-3** using **all remaining AP (max)**.

---

✅ *Tip:* Use `max` only when you want BAAS to automatically exhaust available stamina on that level, otherwise specify explicit sweep counts for controlled execution.
