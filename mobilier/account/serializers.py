from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class UserSerializer(serializers.ModelSerializer):
    # On va chercher les données dans la table liée 'profile'
    role = serializers.CharField(source='profile.role', read_only=True)
    telephone = serializers.CharField(source='profile.telephone', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'telephone')

class RegisterSerializer(serializers.ModelSerializer):
    # Champs pour le profil (optionnels à l'inscription si tu veux le rôle par défaut)
    telephone = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'telephone')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Extraction du téléphone pour le profil
        telephone = validated_data.pop('telephone', '')
        
        # Création de l'utilisateur natif
        user = User.objects.create_user(**validated_data)
        
        # Mise à jour du profil automatiquement créé par le signal
        user.profile.telephone = telephone
        user.profile.save()
        
        return user
    