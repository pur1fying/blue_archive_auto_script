# 💀 Hardship Map Usage Guide

The **Hardship Map** operates similarly to **Team Logic** and **Normal Figure** modes.  
Some of the difficult maps require **three teams**, all of which share the **same attribute** as the first team assigned for that region.

---

## 🧾 Fill-in Instructions

### ⚠️ Allowed Characters

The **string** you fill in for the slide level **must not contain characters or words other than**:

```

"-", "sss", "present", "task", ",", [numbers]

```

Each segment should be **split by commas (`,`)**.

> ❌ Do **not** include any keywords like `"sss"`, `"present"`, or `"task"` outside of valid syntax.

---

### 🧩 Example 1: Basic Usage

**Input:**
```

15,12-2

```

**Interpretation:**

BAAS will perform calls:
```

15-1, 15-2, 15-3, 12-2

```
and execute according to **Hard Map** settings:
- `sss` → evaluate star completion  
- `present` → collect rewards  
- `task` → perform challenge missions  

---

### 🧩 Example 2: Number + String

**Input:**
```

15-sss-present

```

**Meaning:**
BAAS will run level group **15-1, 15-2, 15-3**  
and execute both `sss` (star evaluation) and `present` (gift collection).

---

### 🧩 Example 3: Two Numbers + Keywords

**Input:**
```

15-3-sss-task

```

**Meaning:**  
This calls **level 15-3** to:
- achieve `sss` rating  
- complete the `task` challenge.

---

### 🧩 Example 4: Complex Case

**Input:**

```
7,8-sss,9-3-task
```

**Meaning:**
- Calls `(7-1, 7-2, 7-3)` → perform `sss`, collect gifts, and complete challenges.  
- Calls `(8-1, 8-2, 8-3)` → perform `sss`.  
- Calls `9-3` → complete the challenge task.

---

## 🧠 System Behaviour

> 🟡 **Note:**  
> BAAS automatically determines whether:
> - a level has already reached **`sss`**, or  
> - a **gift/present** has been collected.  

If either condition is already satisfied, **the level will be skipped automatically** to optimise runtime efficiency.
