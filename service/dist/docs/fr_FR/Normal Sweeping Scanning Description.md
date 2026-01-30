
# 🧹 Guide de configuration du balayage normal

Chaque **configuration de balayage** suit le format général suivant :

```
région - numéro_mission - nombre_balayages
```

---

## 🧩 Structure

| Élément              | Description                      |
| :------------------- | :------------------------------- |
| **Région**           | Identifiant de la carte ou zone. |
| **Numéro mission**   | Niveau ou étape à balayer.       |
| **Nombre balayages** | Nombre d’exécutions du balayage. |

Chaque configuration doit être **séparée par des virgules (`,`)**.

---

## 🗺️ 1. Niveaux disponibles

Toutes les cartes **postérieures à Académie 1 et Académie 5** sont prises en charge pour le balayage automatique.

> 🟡 **Exemple valide :**
>
> ```
> 12-1-3, 13-2-2, 14-4-1
> ```

---

## ⚙️ 2. Description spéciale

Sur le **serveur international**,
le champ `nombre_balayages` peut prendre le mot-clé **`max`**.

* BAAS détermine automatiquement si le niveau peut être terminé, selon :

    * les **points d’action (AP)** actuels,
    * la difficulté du niveau et son statut de complétion.

---

### 🧮 Exemple

Quand l’endurance est suffisante :

```
15-3, 20-3-max
```

**Signification :**

* Balaye **15-3** trois fois.
* Puis balaye **20-3** jusqu’à épuisement de l’endurance (**max**).

---

✅ *Astuce :* Utilisez `max` uniquement si vous souhaitez que BAAS consomme automatiquement toute l’endurance restante sur un niveau. Sinon, indiquez un nombre fixe pour garder le contrôle.
