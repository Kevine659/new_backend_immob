from rest_framework import serializers
from .models import Quartier, BienImmobilier, ImageBien, Profile

class QuartierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quartier
        fields = '__all__'


class ImageBienSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageBien
        fields = ['id', 'image', 'bien']


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'first_name', 'last_name', 'role', 'telephone']


class BienImmobilierSerializer(serializers.ModelSerializer):
    # On utilise ProfileSerializer en lecture seule pour récupérer les détails du bailleur
    bailleur = ProfileSerializer(read_only=True)
    # Et pour l'écriture (POST/PUT), on garde un champ ID optionnel :
    bailleur_id = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(), 
        source='bailleur', 
        write_only=True, 
        required=False, 
        allow_null=True
    )
    
    images = ImageBienSerializer(many=True, read_only=True)

    class Meta:
        model = BienImmobilier
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        is_admin = user and (user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'ADMIN'))

        if is_admin:
            if not validated_data.get('bailleur'):
                raise serializers.ValidationError({"bailleur": "En tant qu'administrateur, vous devez sélectionner un bailleur."})
        else:
            if user and hasattr(user, 'profile'):
                validated_data['bailleur'] = user.profile
            else:
                raise serializers.ValidationError({"detail": "Aucun profil bailleur associé à cet utilisateur."})
        
        # Création du bien
        bien = BienImmobilier.objects.create(**validated_data)
        
        # Enregistrement des images
        if request:
            images_files = request.FILES.getlist('uploaded_images') or request.FILES.getlist('images')
            for image_file in images_files[:4]:
                ImageBien.objects.create(bien=bien, image=image_file)
                
        return bien

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        is_admin = user and (user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'ADMIN'))

        # Si l'utilisateur n'est pas admin, on s'assure qu'il ne change pas le bailleur par un autre
        if not is_admin and user and hasattr(user, 'profile'):
            validated_data['bailleur'] = user.profile

        # Mise à jour des champs classiques du bien
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Gestion de l'ajout de nouvelles images lors d'une modification
        if request:
            images_files = request.FILES.getlist('uploaded_images') or request.FILES.getlist('images')
            if images_files:
                for image_file in images_files[:4]:
                    ImageBien.objects.create(bien=instance, image=image_file)

        return instance
    
    
from rest_framework import serializers
from .models import Reservation

class ReservationSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.user.username', read_only=True)
    client_email = serializers.EmailField(source='client.user.email', read_only=True)
    proprietaire_email = serializers.EmailField(source='bien.bailleur.user.email', read_only=True)
    proprietaire_nom = serializers.CharField(source='bien.bailleur.user.username', read_only=True)
    bien_titre = serializers.CharField(source='bien.titre', read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'