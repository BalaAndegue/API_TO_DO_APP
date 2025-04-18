from rest_framework import serializers
from .models import User, Task,InvitedUserOnTask

''' Un serializer dans Django REST Framework a pour but principal de convertir et valider des données. Il agit comme un pont entre des objets complexes (comme des instances de modèles Django) et des formats simples (comme JSON, que les API utilisent). Voici ses rôles clés :
a. Conversion des données

    Données en entrée : Convertit des données brutes reçues (JSON, formulaire, etc.) en un format Python utilisable, et valide ces données.

    Données en sortie : Convertit des objets Python (instances de modèles, Querysets, etc.) en format JSON pour les rendre lisibles pour un client API.

b. Validation des données

    Les serializers sont utilisés pour valider des données avant de les traiter ou de les insérer dans une base de données.

    Ils permettent de s’assurer que les données respectent certaines règles, comme la longueur d’un champ, un format d’email valide, ou des contraintes spécifiques (exemple : un mot de passe suffisamment complexe).'''




class UserSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField(required=False)  # Champ facultatif

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'profile_photo']
        extra_kwargs = {'password': {'write_only': True}}  # Masque le mot de passe dans les réponses

    def create(self, validated_data):
        profile_photo = validated_data.pop('profile_photo', None)  # Récupérer l'image sans erreur
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        if profile_photo:  # Si l’utilisateur a envoyé une image, l’ajouter
            user.profile_photo = profile_photo
            user.save()
        return user


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'  # Inclure tous les champs
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']  # Ces champs sont automatiques

    def create(self, validated_data):
        request = self.context.get('request')  # Récupérer l'utilisateur
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user  # Associer l’utilisateur connecté
            return Task.objects.create(**validated_data)
        raise serializers.ValidationError("L'utilisateur doit être authentifié pour créer une tâche.")





class InvitedUserOnTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitedUserOnTask
        fields = '__all__'
        read_only_fields = ['inviter', 'invited_at']  # ✅ L’utilisateur qui invite est ajouté automatiquement

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['inviter'] = request.user  # Associe l’invitation à l’utilisateur connecté
            return InvitedUserOnTask.objects.create(**validated_data)
        raise serializers.ValidationError("L'utilisateur doit être authentifié pour inviter quelqu'un.")
