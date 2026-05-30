# 🧩 Auto Clear Mainline Plot Settings

### 🎮 Autoplay and Battle Notes

**Autoplay** can help you **walk through the grid** automatically.  
However, **some battles in the Final Episode cannot be fought automatically.**

---

### 📘 Episode Numbering

| Number | Episode Name  |
|:------:|:--------------|
|   1    | Episode I     |
|   2    | Episode II    |
|   3    | Episode III   |
|   4    | Episode IV    |
|   5    | Final Episode |
|   6    | Episode V     |

---

### 🔢 Input Format

Use a comma (`,`) to separate the numbers indicating each episode to be cleared.

**Example:**

```text
1,2,3
```

This means the script will clear **Episode I → Episode II → Episode III** sequentially.

---

### ⚙️ Default Configuration

If the input box is left empty and you click **“Run”**, the default sequence is used:

| Region | Default Episodes |
|:-------|:-----------------|
| CN     | `1,2,3,4`        |
| Global | `1,2,3,4,5,4`    |
| JP     | `1,2,3,4,5,4,6`  |

