
# 💀 Guide d’utilisation des cartes de difficulté

La **carte de difficulté** fonctionne de manière similaire aux modes **Logique d’équipe** et **Carte normale**.
Certaines cartes difficiles nécessitent **trois équipes**, partageant toutes **le même attribut** que la première équipe assignée à cette région.

---

## 🧾 Instructions de remplissage

### ⚠️ Caractères autorisés

La **chaîne** que vous saisissez pour le niveau de la diapositive **ne doit contenir aucun caractère ou mot autre que** :

```
"-", "sss", "present", "task", ",", [nombres]
```

Chaque segment doit être **séparé par des virgules (`,`)**.

> ❌ N’incluez **aucun mot-clé** comme `"sss"`, `"present"` ou `"task"` en dehors d’une syntaxe valide.

---

### 🧩 Exemple 1 : Utilisation de base

**Entrée :**

```
15,12-2
```

**Interprétation :**

BAAS exécutera les appels suivants :

```
15-1, 15-2, 15-3, 12-2
```

et appliquera les paramètres de la **carte difficile** :

* `sss` → évaluation du score maximal
* `present` → collecte des récompenses
* `task` → exécution des missions spéciales

---

### 🧩 Exemple 2 : Nombre + chaîne

**Entrée :**

```
15-sss-present
```

**Signification :**
BAAS exécutera le groupe de niveaux **15-1, 15-2, 15-3**
et réalisera à la fois l’évaluation `sss` (score maximal) et la collecte `present` (cadeaux).

---

### 🧩 Exemple 3 : Deux nombres + mots-clés

**Entrée :**

```
15-3-sss-task
```

**Signification :**
BAAS appellera **le niveau 15-3** pour :

* obtenir la note `sss`,
* accomplir la mission `task`.

---

### 🧩 Exemple 4 : Cas complexe

**Entrée :**

```
7,8-sss,9-3-task
```

**Signification :**

* Appelle `(7-1, 7-2, 7-3)` → réalise `sss`, collecte les cadeaux et accomplit les missions.
* Appelle `(8-1, 8-2, 8-3)` → réalise uniquement `sss`.
* Appelle `9-3` → accomplit la mission `task`.

---

## 🧠 Comportement du système

> 🟡 **Remarque :**
> BAAS détermine automatiquement si :
>
> * un niveau a déjà atteint **`sss`**, ou
> * un **cadeau (present)** a déjà été collecté.

Si l’une de ces conditions est remplie, **le niveau sera ignoré automatiquement** afin d’optimiser le temps d’exécution.
