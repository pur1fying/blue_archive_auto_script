# 📊 Description of Normal Graphs

---

## 🧩 1. Description of Use

### (1) Unlock and Autofight Requirement

You **must enable** both:

- 🟡 **Unlock Automatically End Rounds**
- 🟡 **Autofight**

> The system will automatically detect and enable these functions if possible.

---

### (2) Supported Levels

Supported mainline ordinary levels:  
🟡 **4 – 25**

---

### (3) Movement Logic

When BAAS slides are fixed, all team movements are executed with **a single click**.  
Because the number of teams in *Blue Archive* slides varies,  
the **numbering coordinates** and **movement order** also differ depending on the team composition.

---

### (4) Automatic Extrapolation Notes

When performing **automatic extrapolation**,  
🟡 **you must ensure that smaller-numbered teams and larger-numbered teams are correctly assigned.**  
(If uncertain, double-check team numbering before proceeding.)

---

### (5) Normal Thumbnail Settings

BAAS will determine configurations based on:

- 🟢 **< Normal Thumbnail Settings >**
- 🟢 **Selected Group Properties**
- 🟢 **♪ Team Logic ♪**

These determine the correct configuration for each slide.

> The first corresponding property in the diagrams is **[1]**, and the second is **[2]**.

---

## 🤖 2. Team Logic

1. Prioritize team selection based on **restraint relationships** (counter relationships),  
   gradually reducing reliance on attribute matching for remaining opponents.
2. When selecting a team:  
   `4 - (team number) >= number of remaining required teams`.
3. If neither condition (1) nor (2) can be satisfied, gradually weaken the restraint relationships among [1] counterparts.
4. If some teams are already selected and `4 - max(selected teams) >= remaining teams required`,  
   fill the remaining with **optional numbers**.
5. If none of the above conditions are met, default to **team 1, 2, 3**.

---

### 🧠 Example

Selecting order for **23 [Explosion, Crossing] Task Force**:

- One team, one operation.
- If *Explosion team 3* is not selected in the above order, select **4** as the second.
- If still unavailable, choose **12** as the final team.

---

## 🚀 3. Description of Normal Graph Push-Chart Level

### (1) Area Push Behavior

If you encounter  
🟡 **“Could not close temporary folder: %s”**,  
each entered number represents an **area to be pushed**.  
The program will check whether each level within that area should be replayed  
based on whether the current level has reached an `SSS` rating.

**Example:**
```text
15, 16, 14
```

This means the program will roll through areas **15 → 16 → 14** sequentially.

---

### (2) Mandatory Hit Configuration

If 🟡 **Enable Mandatory Hits at Each Specified Level** is turned on:

- Enter a single number → push one entire area once.
- Enter `number-number` → specify an exact sub-level.

**Example:**

```text
15, 16-3
```

---

✅ *Tip:* Always verify that level numbering and team assignments align with your **BAAS configuration** before running automated scripts to prevent mismatched behavior.

