
# 📊 Description des cartes normales

---

## 🧩 1. Description d’utilisation

### (1) Déblocage et combat automatique requis

Vous **devez activer** :

* 🟡 **Débloquer automatiquement les manches terminées**
* 🟡 **Combat automatique**

> Le système détectera et activera automatiquement ces fonctions si possible.

---

### (2) Niveaux pris en charge

Niveaux principaux normaux pris en charge :
🟡 **4 – 25**

---

### (3) Logique de mouvement

Lorsque les diapositives BAAS sont fixées, tous les mouvements d’équipe sont exécutés en **un seul clic**.
Comme le nombre d’équipes dans *Blue Archive* varie,
les **coordonnées numérotées** et **l’ordre des mouvements** diffèrent selon la composition.

---

### (4) Notes sur l’extrapolation automatique

Lors de l’**extrapolation automatique**,
🟡 **assurez-vous que les équipes à petits numéros et à grands numéros sont correctement assignées.**
(En cas de doute, revérifiez la numérotation avant de continuer.)

---

### (5) Paramètres des miniatures normales

BAAS détermine les configurations en se basant sur :

* 🟢 **< Paramètres des miniatures normales >**
* 🟢 **Propriétés du groupe sélectionné**
* 🟢 **♪ Logique d’équipe ♪**

Ces éléments définissent la configuration correcte pour chaque diapositive.

> La première propriété correspondante dans les diagrammes est **[1]**, la seconde **[2]**.

---

## 🤖 2. Logique d’équipe

1. Prioriser la sélection d’équipe selon les **relations de contre-attaque**.
2. Lors de la sélection : `4 - (numéro d’équipe) >= nombre d’équipes restantes requises`.
3. Si les conditions (1) et (2) échouent, réduire progressivement les contraintes entre homologues [1].
4. Si certaines équipes sont déjà choisies et `4 - max(sélectionnées) >= restantes`,
   compléter avec des **numéros optionnels**.
5. Sinon, par défaut : **équipes 1, 2, 3**.

---

### 🧠 Exemple

Ordre de sélection pour **23 [Explosion, Croisement] Task Force** :

* Une équipe, une opération.
* Si *Équipe Explosion 3* n’est pas choisie, sélectionner **4** en second.
* Sinon, **12** en dernier.

---

## 🚀 3. Description du niveau de progression des cartes normales

### (1) Comportement de progression

Si vous rencontrez
🟡 **« Impossible de fermer le dossier temporaire : %s »**,
chaque nombre représente une **zone à parcourir**.
Le programme vérifie si chaque niveau doit être rejoué selon le score `SSS`.

**Exemple :**

```text
15, 16, 14
```

Signifie : **15 → 16 → 14** séquentiellement.

---

### (2) Configuration des coups obligatoires

Si 🟡 **Activer les coups obligatoires** est activé :

* Un seul nombre → parcourir toute la zone.
* `nombre-nombre` → sous-niveau exact.

**Exemple :**

```text
15, 16-3
```

---

✅ *Astuce :* Vérifiez toujours la numérotation et les équipes avant d’exécuter les scripts automatiques BAAS.
