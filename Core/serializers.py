from rest_framework import serializers
from .models import User

''' Un serializer dans Django REST Framework a pour but principal de convertir et valider des données. Il agit comme un pont entre des objets complexes (comme des instances de modèles Django) et des formats simples (comme JSON, que les API utilisent). Voici ses rôles clés :
a. Conversion des données

    Données en entrée : Convertit des données brutes reçues (JSON, formulaire, etc.) en un format Python utilisable, et valide ces données.

    Données en sortie : Convertit des objets Python (instances de modèles, Querysets, etc.) en format JSON pour les rendre lisibles pour un client API.

b. Validation des données

    Les serializers sont utilisés pour valider des données avant de les traiter ou de les insérer dans une base de données.

    Ils permettent de s’assurer que les données respectent certaines règles, comme la longueur d’un champ, un format d’email valide, ou des contraintes spécifiques (exemple : un mot de passe suffisamment complexe).'''
class UserSerializer(serializers.ModelSerializer):
    #pour cnvertir en json les objets django et vis versa pour la creation d'un utilisateur via API"
    password = serializers.CharField(write_only=True)  # Empêche la lecture du mot de passe

    class Meta:
        #model = User
        fields = ['username', 'password', 'email']  # Inclure les champs nécessaires

    def create(self, validated_data):
        # Crée un utilisateur avec un mot de passe haché
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],   #ici si la cle n'existe pas une erreur est genere
            email=validated_data.get('email', ''),  #ici si la cle n'existe pas une valeur par defaut lui est assigne dans notre cas c'est ""
            role = validated_data.get('role', ''),
        )

        #gerons les champs 'profile_photo' separemment 
        if 'profile_photo' in validated_data:
            user.profile_photo = validated_data['profile_photo']
            user.save()
        return user