# 🕒 Scheduling Configuration Filling Guide

This guide explains how to correctly fill in and interpret scheduling configuration fields for automated task execution.

---

## ⚙️ 1. Priority

When multiple tasks exist in the queue:

- Tasks with **lower priority values** are executed **first**.

> Example:  
> Task A (priority 1) runs before Task B (priority 2).

---

## ⏳ 2. Execution Interval

- **Integer `0`** means the task repeats **every day** (one-day interval).  
- Larger integers represent longer gaps between executions (in days).

---

## 🕐 3. Daily Reset

Tasks execute automatically at fixed times each day. This can be easily set on **New UI**.

- **Format:**  

```
[ [ h, m, s ] ]
```

*(UTC time)*

- **Multiple timestamps** can be specified, separated by commas.

**Example:**

```
[ [ 0, 0, 0 ], [ 20, 0, 0 ] ]
```

**Meaning:**  
Runs at **8 AM** and **4 PM Beijing time (UTC + 8)**.

---

## 🚫 4. Disabled Time Periods

Tasks **will not run** during specified disabled time windows. This can also be easily set on **New UI**.

- **Format:**  
```

[ [ [ h1, m1, s1 ], [ h2, m2, s2 ] ] ]

```
*(UTC time)*

- **Multiple periods** may be provided, separated by commas.

**Example:**
```

[ [ [ 0, 0, 0 ], [ 24, 0, 0 ] ] ]

```

**Meaning:**  
Tasks are disabled for the **entire day**.

---

## 🔁 5. Pre-tasks & Post-tasks

You can chain related operations:

- **Pre-tasks:** executed **before** the current task.  
- **Post-tasks:** executed **after** the current task.

> Ensures dependent actions run in correct order within the scheduling system.
