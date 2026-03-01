
# ⚔️ Guide de remplissage des paramètres de balayage d’activité

Ce guide explique comment configurer correctement les **paramètres de balayage d’activité** pour l’automatisation BAAS.

---

## 🧾 Balayer une seule mission

**Paramètre :**
`Numéro de mission à balayer`

* Type : **Entier**
* Plage : de `1` au *niveau de difficulté maximal* de l’activité actuelle.

**Paramètre :**
`Nombre de balayages`

1. **Entier** → indique le *nombre exact de balayages*.
   Exemple : `3` signifie effectuer la mission 3 fois.
2. **Décimal** → indique un *pourcentage des points d’action (AP)* utilisés.
   Exemple : `0.5` signifie utiliser **AP × 0,5** pour le balayage.
3. **Fraction** → indique une *fraction d’AP* à utiliser.
   Exemple : `1/3` signifie utiliser **AP × (1/3)** pour le balayage.

---

## 🔁 Balayer plusieurs missions

Pour balayer plusieurs missions de suite,
séparez leurs numéros par des virgules (`,`).

**Exemple :**

```
Mission : 9, 10, 11
Nombre de balayages : 0.5, 3, 1/3
AP : 999
```

**Interprétation :**

| Mission | Calcul           | Résultat |
| :------ | :--------------- | :------- |
| **9**   | (999 × 0.5) / 20 | 25 fois  |
| **10**  | Fixé à 3         | 3 fois   |
| **11**  | (999 × 1/3) / 20 | 16 fois  |

➡️ BAAS effectuera les balayages dans l’ordre : **9 → 10 → 11**.

---

✅ *Astuce :* Vérifiez toujours que la valeur de vos **AP** correspond à l’endurance disponible avant d’exécuter plusieurs balayages.
