from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Quartier
from .serializers import QuartierSerializer
from .permissions import IsAdminOrStaffUser
from rest_framework.permissions import AllowAny

class QuartierListView(APIView):
    # On autorise tout utilisateur authentifié, 
    # la logique de modification sera gérée dans les méthodes
    permission_classes = [AllowAny]

    def get(self, request):
        """Tout le monde (authentifié) peut voir."""
        quartiers = Quartier.objects.all()
        serializer = QuartierSerializer(quartiers, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Seul l'admin/staff peut enregistrer."""
        if not IsAdminOrStaffUser().has_permission(request, self):
            return Response({"detail": "Accès interdit."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = QuartierSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuartierDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        """Seul l'admin/staff peut modifier."""
        if not IsAdminOrStaffUser().has_permission(request, self):
            return Response({"detail": "Accès interdit."}, status=status.HTTP_403_FORBIDDEN)
        
        quartier = Quartier.objects.get(pk=pk)
        serializer = QuartierSerializer(quartier, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Seul l'admin/staff peut supprimer."""
        if not IsAdminOrStaffUser().has_permission(request, self):
            return Response({"detail": "Accès interdit."}, status=status.HTTP_403_FORBIDDEN)
        
        quartier = Quartier.objects.get(pk=pk)
        quartier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
from rest_framework import generics
from .models import BienImmobilier, Profile
from .serializers import BienImmobilierSerializer
from .permissions import IsAdminOrOwnerOrReadOnly

from rest_framework import generics
from rest_framework.exceptions import ValidationError

class BienImmobilierListCreateView(generics.ListCreateAPIView):
    queryset = BienImmobilier.objects.all()
    serializer_class = BienImmobilierSerializer
    permission_classes = [IsAdminOrOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        
        # Si l'utilisateur n'est pas authentifié (cas de la lecture publique si autorisée)
        if not user.is_authenticated:
            return BienImmobilier.objects.all()
            
        # 1. Administrateur : voit tous les biens
        if user.is_staff or user.is_superuser:
            return BienImmobilier.objects.all()
            
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        if profile:
            # 2. Propriétaire / Bailleur : voit uniquement ses propres biens
            if profile.role == 'PROPRIETAIRE':
                return BienImmobilier.objects.filter(bailleur=profile)
                
            # Si c'est un admin via son profil
            if profile.role == 'ADMIN':
                return BienImmobilier.objects.all()
                
        # Par défaut, s'il n'est ni admin ni propriétaire reconnu, on renvoie rien ou tous selon tes règles de lecture
        return BienImmobilier.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        user = self.request.user
        
        # Vérifie si l'utilisateur est Admin (staff ou rôle ADMIN dans son profile)
        is_admin = user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'ADMIN')

        if is_admin:
            # L'admin doit avoir fourni un bailleur dans la requête
            bailleur_id = self.request.data.get('bailleur')
            if not bailleur_id:
                raise ValidationError({"bailleur": "En tant qu'administrateur, vous devez sélectionner un bailleur."})
            serializer.save() 
        else:
            # Si c'est un propriétaire (PROPRIETAIRE), on le lie automatiquement à son propre profil
            if hasattr(user, 'profile'):
                serializer.save(bailleur=user.profile)
            else:
                raise ValidationError({"detail": "Aucun profil bailleur associé à cet utilisateur."})
            
            
class BienImmobilierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BienImmobilier.objects.all()
    serializer_class = BienImmobilierSerializer
    permission_classes = [AllowAny]
    
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import BienImmobilier, ImageBien
from .serializers import BienImmobilierSerializer, ImageBienSerializer

   
class ImageBienViewSet(viewsets.ModelViewSet):
    queryset = ImageBien.objects.all()
    serializer_class = ImageBienSerializer
    permission_classes = [AllowAny]
    
    
    
from rest_framework import viewsets, permissions
from .models import Reservation
from .serializers import ReservationSerializer
from django.core.exceptions import ObjectDoesNotExist

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        
    def get_queryset(self):
        user = self.request.user
        
        # 1. Administrateur : voit tout
        if user.is_staff or user.is_superuser:
            return Reservation.objects.all()
            
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        if profile:
            # 2. Propriétaire / Bailleur : voit les réservations des biens dont il est le bailleur
            if profile.role == 'PROPRIETAIRE':
                return Reservation.objects.filter(bien__bailleur=profile)
                
            # 3. Client : voit uniquement ses propres réservations
            return Reservation.objects.filter(client=profile)
            
        return Reservation.objects.none()