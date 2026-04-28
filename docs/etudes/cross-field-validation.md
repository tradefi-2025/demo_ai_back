# Validation Croisée entre ParameterDefinitions

## 🎯 Le problème

```
P1 = 10,  P2 = 50,  P3 = 100

Règle : P1 < P2 < P3
```

Comment exprimer et valider cette contrainte **dynamiquement** ?

---

## 🤔 Back ou Front ? → LES DEUX, mais chacun son rôle

```
┌──────────────────────────────────────────────────────────────┐
│                     RÉPARTITION IDÉALE                       │
├──────────────────┬───────────────────────────────────────────┤
│   BACK (Spring)  │  Validation "source de vérité"            │
│                  │  → Toujours exécutée                      │
│                  │  → Protège la BDD                         │
│                  │  → Retourne des erreurs structurées        │
├──────────────────┼───────────────────────────────────────────┤
│   FRONT (Angular)│  Validation UX / feedback immédiat        │
│                  │  → Confort utilisateur                    │
│                  │  → Désactive le bouton Submit             │
│                  │  → Affiche les erreurs en temps réel      │
└──────────────────┴───────────────────────────────────────────┘

         ⚠️  Ne jamais valider SEULEMENT côté front !
```

---

## 🆕 Deux types de paramètres

```
┌────────────────────────────────────────────────────────────┐
│               PARAMÈTRES SANS DÉPENDANCE                   │
│                                                            │
│  constraints: []                                           │
│  → Validation simple : min/max absolus uniquement          │
│  → Ex: "Nombre de jours" entre 1 et 365                   │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│               PARAMÈTRES AVEC DÉPENDANCE                   │
│                                                            │
│  constraints: [ { type: "GREATER_THAN", target: "P1" } ]  │
│  → Validation croisée + min/max absolus (les deux !)       │
│  → Ex: "Take Profit" doit être > "Stop Loss"               │
└────────────────────────────────────────────────────────────┘
```

> 💡 **Pas besoin de flag** `hasDependencies` — la liste `constraints` suffit :
> - `constraints: []`    → pas de dépendance
> - `constraints: [...]` → a des dépendances
    > Un flag serait redondant et risquerait d'être incohérent avec la liste.

---

## 🔢 Ordre d'affichage — Tri Topologique (calculé par le Front)

Pas besoin d'un attribut `order` côté back ! Le front peut **calculer l'ordre automatiquement**
à partir des dépendances — c'est le principe du **tri topologique**.

### 💡 L'idée (récursive)

```
Règle : un paramètre ne peut s'afficher que si tous ses "parents"
        (ceux dont il dépend) ont déjà été affichés avant lui.

→ On commence par ceux qui n'ont aucune dépendance
→ On retire ces paramètres de la liste
→ On recommence jusqu'à ce que tout soit affiché
```

### Exemple concret

```
Paramètres reçus (dans n'importe quel ordre) :
  P2 → dépend de P1 et P3
  P1 → aucune dépendance
  P3 → aucune dépendance

Étape 1 : P1 et P3 n'ont pas de dépendances → affichés en 1er
  → [P1, P3]

Étape 2 : P2 dépendait de P1 et P3, ils sont résolus → P2 peut s'afficher
  → [P1, P3, P2]

Résultat final : [P1, P3, P2]  ✅ calculé sans attribut "order" !
```

### Algorithme (tri topologique)

```typescript
function topologicalSort(fields: FieldConfig[]): FieldConfig[] {
  const resolved = new Set<string>();
  const result: FieldConfig[] = [];
  let remaining = [...fields];

  while (remaining.length > 0) {
    // Prendre tous les champs dont toutes les dépendances sont résolues
    const ready = remaining.filter(f =>
      (f.constraints ?? []).every(c => resolved.has(c.targetParam))
    );

    if (ready.length === 0) {
      // Sécurité : dépendance circulaire détectée
      throw new Error('Dépendance circulaire détectée dans les paramètres');
    }

    ready.forEach(f => {
      resolved.add(f.name);
      result.push(f);
    });

    remaining = remaining.filter(f => !resolved.has(f.name));
  }

  return result;
}
```

### Avantages vs attribut `order` explicite

```
┌─────────────────────────┬──────────────────────────────────┐
│   Attribut "order"      │   Tri topologique                │
├─────────────────────────┼──────────────────────────────────┤
│ ❌ Attribut à gérer     │ ✅ Rien à ajouter au modèle      │
│ ❌ Peut être incohérent │ ✅ Toujours cohérent             │
│    avec les dépendances │    avec les dépendances          │
│ ❌ Limité à 1 niveau    │ ✅ N niveaux de profondeur       │
│ ✅ Simple à comprendre  │ ✅ Détecte les cycles (sécurité) │
└─────────────────────────┴──────────────────────────────────┘
```

---

## 1. 📦 Modèle côté Back (Spring Boot)

```java
// ConstraintType.java (enum)
public enum ConstraintType {
    GREATER_THAN,       // P2 > P1
    LESS_THAN,          // P2 < P3
    GREATER_OR_EQUAL,
    LESS_OR_EQUAL
}
```

```java
// Dans ParameterDefinitionEntity.java
@Column
private Double minValue;   // min absolu (ex: 0)

@Column
private Double maxValue;   // max absolu (ex: 1000)

// contraintes relatives à d'autres paramètres (vide = pas de dépendance)
@OneToMany(mappedBy = "sourceParam", cascade = CascadeType.ALL)
private List<ParameterConstraintEntity> constraints;
```

```java
// ParameterConstraintEntity.java
@Entity
public class ParameterConstraintEntity {

    @ManyToOne
    private ParameterDefinitionEntity sourceParam;  // P2

    @Enumerated(EnumType.STRING)
    private ConstraintType type;                    // GREATER_THAN

    @ManyToOne
    private ParameterDefinitionEntity targetParam;  // P1

    // → exprime : P2 GREATER_THAN P1
}
```

---

## 2. 📡 Ce que le Back envoie au Front (DTO)

```json
[
  {
    "name": "P1",
    "label": "Stop Loss",
    "type": "number",
    "minValue": 0,
    "maxValue": 1000,
    "constraints": []
  },
  {
    "name": "P2",
    "label": "Take Profit",
    "type": "number",
    "minValue": 0,
    "maxValue": 1000,
    "constraints": [
      { "type": "GREATER_THAN", "targetParam": "P1" },
      { "type": "LESS_THAN",    "targetParam": "P3" }
    ]
  },
  {
    "name": "P3",
    "label": "Max Limit",
    "type": "number",
    "minValue": 0,
    "maxValue": 1000,
    "constraints": []
  }
]
```

---

## 3. ⚙️ Logique Front Angular

### Schéma de décision

```
Paramètres reçus du Back
        │
        ▼
  Trier par "order"
        │
        ▼
  Pour chaque paramètre :
        │
        ├── Toujours appliquer min/max absolus (Validators.min / max)
        │
        └── constraints vide ?
              │
              ├── OUI → fin (min/max suffit)
              │
              └── NON → appliquer EN PLUS le cross-field validator
                         (au niveau du FormGroup)
```

### Code Angular

```typescript
buildForm(fields: FieldConfig[]): FormGroup {
  // 1. Calculer l'ordre via tri topologique (pas besoin d'attribut "order")
  const sorted = topologicalSort(fields);

  // 2. Créer les FormControls avec min/max absolus
  const group: any = {};
  sorted.forEach(field => {
    const validators: ValidatorFn[] = [];
    if (field.minValue != null) validators.push(Validators.min(field.minValue));
    if (field.maxValue != null) validators.push(Validators.max(field.maxValue));
    if (field.validators?.required) validators.push(Validators.required);
    group[field.name] = new FormControl('', validators);
  });

  // 3. Ajouter le cross-field validator au FormGroup
  //    seulement si au moins un paramètre a des contraintes
  const hasCrossField = sorted.some(f => f.constraints?.length > 0);
  const formValidators = hasCrossField
    ? [buildCrossFieldValidator(sorted)]
    : [];

  return new FormGroup(group, formValidators);
}
```

```typescript
// Cross-field validator (niveau FormGroup)
function buildCrossFieldValidator(fields: FieldConfig[]): ValidatorFn {
    return (group: AbstractControl): ValidationErrors | null => {
        const errors: ValidationErrors = {};

        fields
            .filter(f => f.constraints?.length > 0)
            .forEach(field => {
                const sourceValue = group.get(field.name)?.value;

                field.constraints.forEach(constraint => {
                    const targetValue = group.get(constraint.targetParam)?.value;
                    if (sourceValue == null || targetValue == null) return;

                    let violated = false;
                    switch (constraint.type) {
                        case 'GREATER_THAN':
                            violated = sourceValue <= targetValue;
                            break;
                        case 'LESS_THAN':
                            violated = sourceValue >= targetValue;
                            break;
                        case 'GREATER_OR_EQUAL':
                            violated = sourceValue < targetValue;
                            break;
                        case 'LESS_OR_EQUAL':
                            violated = sourceValue > targetValue;
                            break;
                    }

                    if (violated) {
                        errors[`${field.name}_${constraint.type}_${constraint.targetParam}`] = {
                            source: field.label,
                            target: constraint.targetParam,
                            type: constraint.type
                        };
                    }
                });
            });

        return Object.keys(errors).length ? errors : null;
    };
}
```

---

## 4. ✅ Validation finale côté Back (Spring Boot)

```java
public void validateParameterValues(List<ParameterValueDTO> values,
                                    List<ParameterDefinitionEntity> definitions) {
    Map<String, Double> valueMap = values.stream()
            .collect(Collectors.toMap(v -> v.getName(), v -> v.getValue()));

    definitions.forEach(def -> {
        Double source = valueMap.get(def.getName());

        // Validation min/max absolus
        if (source != null) {
            if (def.getMinValue() != null && source < def.getMinValue())
                throw new ValidationException(def.getName() + " est inférieur au minimum");
            if (def.getMaxValue() != null && source > def.getMaxValue())
                throw new ValidationException(def.getName() + " dépasse le maximum");
        }

        // Validation croisée (seulement si constraints non vide)
        if (def.getConstraints() == null || def.getConstraints().isEmpty()) return;

        def.getConstraints().forEach(constraint -> {
            Double target = valueMap.get(constraint.getTargetParam().getName());
            if (source == null || target == null) return;

            boolean violated = switch (constraint.getType()) {
                case GREATER_THAN -> source <= target;
                case LESS_THAN -> source >= target;
                case GREATER_OR_EQUAL -> source < target;
                case LESS_OR_EQUAL -> source > target;
            };

            if (violated) {
                throw new ValidationException(
                        def.getName() + " doit être " + constraint.getType()
                                + " " + constraint.getTargetParam().getName()
                );
            }
        });
    });
}
```

---

## 🗺️ Schéma final bout en bout

```
BDD
 └── ParameterDefinition
       ├── P2 : min=0, max=1000, constraints=[P2 > P1, P2 < P3]  ← reçu en 1er
       ├── P1 : min=0, max=1000, constraints=[]
       └── P3 : min=0, max=1000, constraints=[]

         │  GET /api/agent/{id}/parameter-definitions
         ▼
      Angular reçoit [P2, P1, P3] (ordre quelconque)
         │
         ├── topologicalSort()
         │     P1 : pas de dépendances → résolu en 1er
         │     P3 : pas de dépendances → résolu en 1er
         │     P2 : P1 et P3 résolus  → résolu en 2ème
         │   → [P1, P3, P2]
         │
         ├── P1 → Validators.min(0), Validators.max(1000)
         ├── P3 → Validators.min(0), Validators.max(1000)
         └── P2 → Validators.min(0), Validators.max(1000) + cross-field
                    │
                    ▼
             Utilisateur saisit P2 = 5 alors que P1 = 10
                    │
                    ▼
             ❌ Erreur affichée immédiatement côté front
                    │
                    ▼  (si l'utilisateur bypass le front)
             POST /api/agent/{id}/parameters
                    │
                    ▼
             ✅ Spring Boot revalide → rejette avec 400 Bad Request
```






