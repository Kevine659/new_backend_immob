from django.db import models
from account.models import Profile

class Quartier(models.Model):
    """
    Référentiel fixe des quartiers 
    """
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du quartier")
    ville = models.CharField(max_length=100, verbose_name="Nom de la ville")
    latitude_centre = models.FloatField(verbose_name="Latitude du centre")
    longitude_centre = models.FloatField(verbose_name="Longitude du centre")
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = "Quartier"
        verbose_name_plural = "Quartiers"

    def __str__(self):
        return self.nom


class BienImmobilier(models.Model):
    TYPE_CHOICES = [
        ('studio', 'Studio'),
        ('appartement', 'Appartement'),
        ('chambre', 'Chambre'),
        ('maison', 'Maison / Villa'),
        ('terrain', 'Terrain'),
    ]
    
    STATUT_CHOICES = [
        ('louer', 'À Louer'),
        ('vendre', 'À Vendre'),
    ]

    titre = models.CharField(max_length=100, verbose_name="Titre de l'annonce")
    description = models.TextField(verbose_name="Description détaillée")
    prix = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix (FCFA)")
    type_bien = models.CharField(max_length=20, choices=TYPE_CHOICES, default='appartement')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='louer')
    chambres = models.PositiveIntegerField(default=0, verbose_name="Nombre de chambres")
    douches = models.PositiveIntegerField(default=0, verbose_name="Nombre de douches")
    cuisine = models.PositiveIntegerField(default=0, verbose_name="Nombre de cuisine")
    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    
    # Coordonnées pour Leaflet
    latitude = models.FloatField(verbose_name="Latitude", default=0.0)
    longitude = models.FloatField(verbose_name="Longitude", default=0.0)
    
    # Dates
    cree_le = models.DateTimeField(auto_now_add=True)
    
    # RELATIONS
    quartier = models.ForeignKey(Quartier, on_delete=models.PROTECT, related_name='biens')
    bailleur = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, 
        related_name='annonces',
        limit_choices_to={'role': 'PROPRIETAIRE'}, 
        verbose_name="Bailleur / Agent responsable"
    )

    class Meta:
        ordering = ['-cree_le']
        verbose_name = "Bien Immobilier"
        verbose_name_plural = "Biens Immobiliers"

    def __str__(self):
        return f"{self.titre} - {self.quartier.nom}"

class ImageBien(models.Model):
    bien = models.ForeignKey(
        BienImmobilier, 
        on_delete=models.CASCADE, 
        related_name='images', 
        verbose_name="Bien immobilier"
    )
    image = models.ImageField(upload_to='biens/', verbose_name="Image du bien")

    class Meta:
        verbose_name = "Image de bien"
        verbose_name_plural = "Images de biens"

    def __str__(self):
        return f"Image pour {self.bien.titre}"
    
    
from django.db import models
from .models import BienImmobilier, Profile

class Reservation(models.Model):
    client = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reservations')
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE, related_name='reservations')
    proprietaire = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='biens_reserves', null=True, blank=True)
    telephone = models.CharField(max_length=20)
    cree_le = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Associe automatiquement le propriétaire du bien lors de la sauvegarde si le bien est présent
        if self.bien and self.bien.bailleur:
            self.proprietaire = self.bien.bailleur
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Réservation de {self.client} pour {self.bien.titre}"