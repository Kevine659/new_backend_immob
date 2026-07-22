from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ROLE_CHOICES = (
        ('ADMIN', 'Administrateur'),
        ('PROPRIETAIRE', 'Propriétaire'),
        ('LOCATAIRE', 'Locataire'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LOCATAIRE')
    telephone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Signal pour créer le profil automatiquement lors de la création d'un User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()