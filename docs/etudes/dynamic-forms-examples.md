# Validateurs Dynamiques en Angular — Exemples Concrets

---

## 📐 Schéma global de l'idée

```
JSON Config (depuis API ou fichier)
        │
        ▼
┌─────────────────────────────┐
│   Angular Service           │
│   buildForm(config) {       │
│     - crée les FormControl  │
│     - attache les validators│
│   }                         │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│   FormGroup dynamique       │
│   ├── name  [required]      │
│   ├── email [required,email]│
│   └── age   [min:18, max:99]│
└─────────────────────────────┘
        │
        ▼
   Template Angular
   (boucle sur les champs)
```

---

## 1. 🧱 La configuration (le "contrat")

```typescript
// field-config.model.ts
export interface FieldConfig {
    name: string;
    label: string;
    type: 'text' | 'email' | 'number' | 'select';
    validators?: {
        required?: boolean;
        minLength?: number;
        maxLength?: number;
        min?: number;
        max?: number;
        pattern?: string;
        email?: boolean;
    };
    options?: string[]; // pour les select
}
```

---

## 2. ⚙️ Le Service qui construit le formulaire

```typescript
// dynamic-form.service.ts
@Injectable({providedIn: 'root'})
export class DynamicFormService {

    buildForm(fields: FieldConfig[]): FormGroup {
        const group: any = {};

        fields.forEach(field => {
            const validators = this.buildValidators(field.validators);
            group[field.name] = new FormControl('', validators);
        });

        return new FormGroup(group);
    }

    private buildValidators(config: FieldConfig['validators']): ValidatorFn[] {
        if (!config) return [];
        const validators: ValidatorFn[] = [];

        if (config.required) validators.push(Validators.required);
        if (config.email) validators.push(Validators.email);
        if (config.minLength != null) validators.push(Validators.minLength(config.minLength));
        if (config.maxLength != null) validators.push(Validators.maxLength(config.maxLength));
        if (config.min != null) validators.push(Validators.min(config.min));
        if (config.max != null) validators.push(Validators.max(config.max));
        if (config.pattern) validators.push(Validators.pattern(config.pattern));

        return validators;
    }
}
```

---

## 3. 🖥️ Le Composant

```typescript
// dynamic-form.component.ts
@Component({...})
export class DynamicFormComponent implements OnInit {

    form!: FormGroup;

    // Simuler une config reçue (depuis une API par exemple)
    fieldsConfig: FieldConfig[] = [
        {
            name: 'username',
            label: "Nom d'utilisateur",
            type: 'text',
            validators: {required: true, minLength: 3}
        },
        {
            name: 'email',
            label: 'Email',
            type: 'email',
            validators: {required: true, email: true}
        },
        {
            name: 'age',
            label: 'Âge',
            type: 'number',
            validators: {required: true, min: 18, max: 99}
        }
    ];

    constructor(private dynamicFormService: DynamicFormService) {
    }

    ngOnInit() {
        this.form = this.dynamicFormService.buildForm(this.fieldsConfig);
    }

    onSubmit() {
        if (this.form.valid) {
            console.log(this.form.value);
        }
    }
}
```

---

## 4. 🎨 Le Template HTML

```html
<!-- dynamic-form.component.html -->
<form [formGroup]="form" (ngSubmit)="onSubmit()">

    <div *ngFor="let field of fieldsConfig">
        <label>{{ field.label }}</label>

        <!-- Champ texte / email / number -->
        <input
                *ngIf="field.type !== 'select'"
                [type]="field.type"
                [formControlName]="field.name"
        />

        <!-- Champ select -->
        <select *ngIf="field.type === 'select'" [formControlName]="field.name">
            <option *ngFor="let opt of field.options" [value]="opt">{{ opt }}</option>
        </select>

        <!-- Messages d'erreur dynamiques -->
        <div *ngIf="form.get(field.name)?.invalid && form.get(field.name)?.touched">
            <span *ngIf="form.get(field.name)?.errors?.['required']">Champ obligatoire</span>
            <span *ngIf="form.get(field.name)?.errors?.['email']">Email invalide</span>
            <span *ngIf="form.get(field.name)?.errors?.['minlength']">Trop court</span>
            <span *ngIf="form.get(field.name)?.errors?.['min']">Valeur trop petite</span>
        </div>
    </div>

    <button type="submit" [disabled]="form.invalid">Envoyer</button>
</form>
```

---

## 5. ⚡ Validateur conditionnel (selon un autre champ)

```
Scénario : si "hasAddress" est coché → "street" devient obligatoire
```

```typescript
this.form.get('hasAddress')!.valueChanges.subscribe(checked => {
    const street = this.form.get('street')!;

    if (checked) {
        street.setValidators([Validators.required]);   // ← on ajoute
    } else {
        street.clearValidators();                      // ← on retire
    }

    street.updateValueAndValidity(); // ← OBLIGATOIRE pour déclencher la réévaluation
});
```

---

## 🔗 Le lien avec Spring Boot (backend)

```
┌─────────────────────────────────────────────────┐
│                   SPRING BOOT                   │
│                                                 │
│  GET /api/forms/agent-config                    │
│  → retourne un JSON décrivant le formulaire     │
│    avec les champs ET les règles de validation  │
└─────────────────────────────────────────────────┘
                        │
                        │  HTTP Response (JSON)
                        ▼
┌─────────────────────────────────────────────────┐
│                   ANGULAR                       │
│                                                 │
│  1. Reçoit le JSON                              │
│  2. buildForm(json)  →  crée le FormGroup       │
│  3. Affiche le formulaire                       │
│  4. Les validateurs sont déjà configurés !      │
└─────────────────────────────────────────────────┘
```

**Exemple du JSON retourné par Spring Boot :**

```json
[
  {
    "name": "agentName",
    "label": "Nom de l'agent",
    "type": "text",
    "validators": {
      "required": true,
      "minLength": 3
    }
  },
  {
    "name": "frequency",
    "label": "Fréquence",
    "type": "select",
    "options": [
      "DAILY",
      "WEEKLY",
      "MONTHLY"
    ],
    "validators": {
      "required": true
    }
  },
  {
    "name": "threshold",
    "label": "Seuil",
    "type": "number",
    "validators": {
      "min": 0,
      "max": 100
    }
  }
]
```

