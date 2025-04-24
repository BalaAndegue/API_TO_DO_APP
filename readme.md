# 📌 API_TO_DO_APP   

## 📝 Description du projet  
TO_DO_APP est une application complète de gestion des tâches conçue pour améliorer la productivité des utilisateurs en leur permettant d’organiser leurs tâches efficacement.  

### 🔹 **Principales caractéristiques :**  
- 📱 **Interface utilisateur intuitive et responsive** (mobile et desktop).  
- ⚙️ **Backend robuste** basé sur Django avec une **API RESTful**.  
- 🗄️ **Base de données SQLite3** pour la persistance des données.  
- 🔐 **Authentification sécurisée** des utilisateurs via **AuthToken**.  
- ✏️ **CRUD complet** : création, lecture, mise à jour et suppression des tâches.  
- 🔄 **Gestion des permissions** pour sécuriser l’accès aux données.  
- 🚀 **Déploiement en production** sur **PythonAnywhere**.  

---

## ⚙️ Installation et Configuration  

### **Prérequis**  
Avant d’installer l’application, assure-toi d’avoir :  
- ✅ **Python 3.x** installé.  
- ✅ **Django** et les dépendances listées dans `requirements.txt`.  
- ✅ Un accès à **PythonAnywhere** pour le déploiement.  

### **Installation et démarrage**  
#### 1️⃣ **Cloner le projet**  
```sh
git clone https://github.com/BalaAndegue/API_TO_DO_APP.git
cd API_TO_DO_APP
```
#### 2️⃣ **Créer un environnement virtuel et installer les dépendances**  
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
#### 3️⃣ **Appliquer les migrations**  
```sh
python manage.py makemigrations
python manage.py migrate
```
#### 4️⃣ **Lancer le serveur**  
```sh
python manage.py runserver
```
✅ **Accède à l’application via `http://127.0.0.1:8000/`**  

---

## 🏗️ **Architecture du projet Django**  

TO_DO_APP est organisé en plusieurs **apps** pour une meilleure modularité.  

### **Structure des dossiers**  
```
API_TO_DO_APP/
│── AuthentificationProjet         # Gestion des tâches
  │── AuthentificationProjet/          #application principale
  │── Core/        # application contenant , tous les models , les serialisers et les vues 
  │── ressources/              # pour les imges et 
  │──static/     # pour les fichiers static css javascript
  │──templates/   # contenat les fchier html pour les test cote front de nos api 
  │── requirements.txt   # Liste des dépendances
  │── manage.py          # Commande principale de Django
  │── Category.md        # EXplique la creation de l'api Category
  │── User.md          
  │── Task.md          
  │── swagger.md
  │── db.sqlite3      # BAse de donnée 



```

### **Composants principaux**  
- **`models.py`** → Définition des modèles (`Task`, `User`,`Category`,`InvitedUserOnTask`,`Context` .).  
- **`serializers.py`** → Sérialisation des objets pour l’API REST.  
- **`views.py`** → Logique métier et endpoints API.  
- **`urls.py`** → Routage des requêtes.  

---

## 🔐 **Authentification et Gestion des Permissions**  

### **Authentification :**  
- 🔑 **AuthToken** est utilisé pour sécuriser les requêtes API.  
- 🔒 Un utilisateur doit être **authentifié** pour accéder à ses tâches.  

### **Permissions :**  
- 🛑 Un utilisateur **ne peut modifier que ses propres tâches**.  
- 🏗️ **Les administrateurs** peuvent voir toutes les tâches.  

---

## 📌 **API REST : Endpoints disponibles**  

### 🔹 **Gestion des utilisateurs**  
| Méthode | Endpoint | Description |
|---------|---------|-------------|
| `POST`  | `/api/register/`  | Enregistrement d'un utilisateur |
| `POST`  | `/api/login/`  | Connexion avec AuthToken |


### 🔹 **Gestion des tâches**  
| Méthode | Endpoint | Description |
|---------|---------|-------------|
| `POST`  | `/api/tasks/`  | Créer une nouvelle tâche |
| `GET`   | `/api/tasks/`  | Lister toutes les tâches de l'utilisateur |
| `PUT`   | `/api/tasks/<id>/`  | Modifier une tâche |
| `DELETE`| `/api/tasks/<id>/`  | Supprimer une tâche |


### 🔹 **Gestion des caregories**  
| Méthode | Endpoint | Description |
|---------|---------|-------------|
| `POST`  | `/api/categories/`  | Créer une nouvelle caregories|
| `GET`   | `/api/categories/`  | Lister toutes les caregories de l'utilisateur |
| `PUT`   | `/api/categories/<id>/`  | Modifier une caregories |
| `DELETE`| `/api/categories/<id>/`  | Supprimer une caregories |

### 🔹 **Gestion des caregories**  
| Méthode | Endpoint | Description |
|---------|---------|-------------|
| `POST`  | `/api/invitations/`  | Créer une nouvelle invitations|
| `GET`   | `/api/invitations/`  | Lister toutes les invitations de l'utilisateur |
| `PUT`   | `/api/invitations/<id>/`  | Modifier une invitations |
| `DELETE`| `/api/invitations/<id>/`  | Supprimer une invitations |



## 📌 Documentation API avec Swagger  

TO_DO_APP fournit une documentation interactive via Swagger pour tester facilement les endpoints API.  

📌 **Accès à la documentation Swagger :**  
- 🔹 **UI Swagger :** [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)  
- 🔹 **Version Redoc :** [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)  

### 🔹 **Tester les endpoints directement via Swagger**  
1️⃣ Ouvrir [Swagger UI](http://127.0.0.1:8000/swagger/)  
2️⃣ Parcourir les différents endpoints et leur documentation  
3️⃣ Faire des requêtes directement depuis l’interface  
4️⃣ Analyser les réponses API et teste les fonctionnalités


---

## 🚀 **Déploiement sur PythonAnywhere**  

### **Étapes du déploiement**  
1️⃣ **Créer un compte PythonAnywhere**  
2️⃣ **Uploader le code source** sur le serveur  
3️⃣ **Installer les dépendances** (`pip install -r requirements.txt`)  
4️⃣ **Appliquer les migrations** (`python manage.py migrate`)  
5️⃣ **Configurer le serveur web** et définir les variables d’environnement  
6️⃣ **Lancer l’application en production**  

## L'API est déplyé sur pythonanywhere et est disponible via les endpoints :
* [http://127.0.0.1:8000/api/](https://aaacode.pythonanywhere.com/api/)
* [http://127.0.0.1:8000/swagger/](https://aaacode.pythonanywhere.com/swagger/)
* [http://127.0.0.1:8000/api/login/](https://aaacode.pythonanywhere.com/api/login/)
* [http://127.0.0.1:8000/api/register/](https://aaacode.pythonanywhere.com/api/register/)
* [http://127.0.0.1:8000/api/tasks/](https://aaacode.pythonanywhere.com/api/tasks)
* [http://127.0.0.1:8000/api/context/](https://aaacode.pythonanywhere.com/api/context)
---

## Test des endpointnécessitant une permission authentification Token
* connecté (login) un client et recupérer son token
* Dans la partir Authorized entrer Token <ton token>
## 🎯 **Fonctionnalités Bonus**  

Ces fonctionnalités apportent une meilleure expérience utilisateur :  
✅ **Partage de tâches entre utilisateurs**.  
✅ **Notifications (email ou push)** pour les rappels.  
✅ **Recherche et filtrage avancés** des tâches.  

---


