
# 🕒 Guide de remplissage de la configuration de planification

Ce guide explique comment remplir et interpréter correctement les champs de configuration de planification pour l’exécution automatique des tâches.

---

## ⚙️ 1. Priorité

Lorsque plusieurs tâches sont dans la file d’attente :

* Les tâches avec une **valeur de priorité plus faible** s’exécutent **en premier**.

> Exemple :
> La tâche A (priorité 1) sera exécutée avant la tâche B (priorité 2).

---

## ⏳ 2. Intervalle d’exécution

* **Entier `0`** → la tâche se répète **chaque jour** (intervalle d’un jour).
* Des entiers plus grands représentent des intervalles plus longs (en jours).

---

## 🕐 3. Réinitialisation quotidienne

Les tâches s’exécutent automatiquement à des heures fixes chaque jour.
Ceci peut être facilement défini dans la **nouvelle interface (New UI)**.

**Format :**

```
[ [ h, m, s ] ]
```

*(Temps UTC)*

Vous pouvez spécifier **plusieurs horaires**, séparés par des virgules.

**Exemple :**

```
[ [ 0, 0, 0 ], [ 20, 0, 0 ] ]
```

**Signification :**
S’exécute à **8 h et 16 h heure de Pékin (UTC +8)**.

---

## 🚫 4. Périodes désactivées

Les tâches **ne s’exécuteront pas** pendant les plages horaires spécifiées.
Elles peuvent aussi être définies facilement dans la **nouvelle interface (New UI)**.

**Format :**

```
[ [ [ h1, m1, s1 ], [ h2, m2, s2 ] ] ]
```

*(Temps UTC)*

Vous pouvez définir **plusieurs périodes**, séparées par des virgules.

**Exemple :**

```
[ [ [ 0, 0, 0 ], [ 24, 0, 0 ] ] ]
```

**Signification :**
Les tâches sont désactivées pour **toute la journée**.

---

## 🔁 5. Tâches préalables et ultérieures

Vous pouvez enchaîner des opérations liées :

* **Pré-tâches :** exécutées **avant** la tâche actuelle.
* **Post-tâches :** exécutées **après** la tâche actuelle.

> Cela garantit que les actions dépendantes s’exécutent dans le bon ordre au sein du système de planification.
