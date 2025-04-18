## 📘 `user.md` – Documentation de l’API Utilisateur

### 🔐 Authentification

Certaines routes nécessitent un **token JWT** dans l’en-tête :

```
Authorization: Bearer <votre_token>
```

---

### 📅 Inscription (Register)

- **URL** : `/api/users/register/`
- **Méthode** : `POST`
- **Accès** : Public

#### Payload
```json
{
  "username": "toto",
  "email": "toto@email.com",
  "password": "monmdp123",
  "phone_number": "0600000000"
}
```

#### Réponse (201)
```json
{
  "id": 1,
  "username": "toto",
  "email": "toto@email.com"
}
```

---

### 🔑 Connexion (Login)

- **URL** : `/api/users/login/`
- **Méthode** : `POST`
- **Accès** : Public

#### Payload
```json
{
  "username": "toto",
  "password": "monmdp123"
}
```

#### Réponse (200)
```json
{
  "access": "JWT_TOKEN",
  "refresh": "REFRESH_TOKEN"
}
```

---

### 👤 Voir son profil

- **URL** : `/api/users/me/`
- **Méthode** : `GET`
- **Accès** : Authentifié

#### Réponse
```json
{
  "id": 1,
  "username": "toto",
  "email": "toto@email.com",
  "phone_number": "0600000000",
  "avatar": "http://.../media/avatar.jpg"
}
```

---

### ✏️ Modifier son profil

- **URL** : `/api/users/me/`
- **Méthode** : `PUT` ou `PATCH`
- **Accès** : Authentifié

#### Payload (ex. avec PATCH)
```json
{
  "phone_number": "0707070707"
}
```

#### Réponse
```json
{
  "id": 1,
  "username": "toto",
  "email": "toto@email.com",
  "phone_number": "0707070707"
}
```

---

### ❌ Supprimer son compte

- **URL** : `/api/users/me/`
- **Méthode** : `DELETE`
- **Accès** : Authentifié

#### Réponse
```json
{
  "detail": "Votre compte a été supprimé."
}
```

