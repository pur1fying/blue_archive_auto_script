
# 🧩 Paramètres d’effacement automatique du scénario principal

### 🎮 Lecture automatique et remarques sur les combats

**La lecture automatique** peut vous aider à **parcourir automatiquement la grille**.
Cependant, **certaines batailles de l’épisode final ne peuvent pas être effectuées automatiquement.**

---

### 📘 Numérotation des épisodes

| Numéro | Nom de l’épisode |
| :----: | :--------------- |
|    1   | Épisode I        |
|    2   | Épisode II       |
|    3   | Épisode III      |
|    4   | Épisode IV       |
|    5   | Épisode final    |
|    6   | Épisode V        |

---

### 🔢 Format d’entrée

Utilisez une virgule (`,`) pour séparer les numéros indiquant les épisodes à effacer.

**Exemple :**

```text
1,2,3
```

Cela signifie que le script effacera **Épisode I → Épisode II → Épisode III** séquentiellement.

---

### ⚙️ Configuration par défaut

Si la zone de saisie est laissée vide et que vous cliquez sur **« Exécuter »**, la séquence par défaut est utilisée :

| Région | Épisodes par défaut |
| :----- | :------------------ |
| CN     | `1,2,3,4`           |
| Global | `1,2,3,4,5,4`       |
| JP     | `1,2,3,4,5,4,6`     |
