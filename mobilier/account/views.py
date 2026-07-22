from django.shortcuts import render

# Create your views here.
import requests
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate          
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from django.shortcuts import get_object_or_404


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Code requis'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Échanger le code d'autorisation contre un access token Google
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': 'http://localhost:5174/auth/google/callback', # Doit être identique à la console Google
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        if 'error' in token_json:
            return Response({'error': 'Échec de la validation du code auprès de Google', 'details': token_json}, status=status.HTTP_400_BAD_REQUEST)

        access_token = token_json.get('access_token')

        # 2. Récupérer les informations de l'utilisateur chez Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_info_response = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
        user_info = user_info_response.json()

        email = user_info.get('email')
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')

        if not email:
            return Response({'error': 'Impossible de récupérer l\'email depuis Google'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Gérer l'utilisateur dans la table User de Django
        try:
            # On cherche si l'utilisateur existe déjà via son email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # S'il n'existe pas, on le crée en générant un username unique basé sur l'email
            username = email.split('@')[0]
            # S'assurer de l'unicité du username
            if User.objects.filter(username=username).exists():
                username = f"{username}_{User.objects.count()}"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

        # 4. Générer ou récupérer le Token d'authentification Django
        token, created = Token.objects.get_or_create(user=user)

        serializer = UserSerializer(user)

        return Response({
            'token': token.key,
            'user': {
                **serializer.data,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        })
                
        


class RegisterView(APIView):
    permission_classes = [AllowAny] # Permet à tout le monde d'accéder à l'inscription

    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        # 1. Validation de base
        if not name or not email or not password:
            return Response(
                {'error': 'Tous les champs sont requis.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 6:
            return Response(
                {'error': 'Le mot de passe doit contenir au moins 6 caractères.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Vérifier si l'adresse email est déjà enregistrée
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Cette adresse e-mail est déjà utilisée.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Générer un username unique à partir de l'e-mail
        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count()}"

        try:
            # 4. Création de l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name # On enregistre le nom saisi dans le champ first_name
            )

            # 5. Génération automatique du Token d'authentification
            token, created = Token.objects.get_or_create(user=user)

            # 6. Réponse de succès avec le token de connexion
            serializer = UserSerializer(user)

            return Response({
                'token': token.key,
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': 'Une erreur est survenue lors de la création du compte.', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            



class LoginView(APIView):
    permission_classes = [AllowAny] # Permet à tout le monde de tenter de se connecter

    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        # 1. Validation des champs
        if not email or not password:
            return Response(
                {'error': 'Veuillez fournir un e-mail et un mot de passe.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Récupérer le username associé à cet email
        try:
            user_exist = User.objects.get(email=email)
            username = user_exist.username
        except User.DoesNotExist:
            # Sécurité : on donne un message générique pour éviter d'indiquer si un email existe ou non
            return Response(
                {'error': 'Identifiants incorrects.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Authentification de l'utilisateur
        user = authenticate(username=username, password=password)

        if user is not None:
            if not user.is_active:
                return Response(
                    {'error': 'Ce compte a été désactivé.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # 4. Récupérer ou générer le Token d'authentification
            token, created = Token.objects.get_or_create(user=user)

            # 5. Réponse de succès
            serializer = UserSerializer(user)

            return Response({
                'token': token.key,
                'user': {
                    **serializer.data,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Identifiants incorrects.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        # Renvoie simplement l'utilisateur actuellement connecté grâce au Token
        return self.request.user
    
    
    
    
    
    
    
    from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer

from rest_framework.permissions import IsAdminUser # Importe la permission admin

class UserListView(APIView):
    # Restreint l'accès aux utilisateurs ayant is_staff=True dans la table User
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Création de l'utilisateur
            user = User.objects.create_user(
                username=request.data.get('email').split('@')[0],
                email=request.data.get('email'),
                first_name=request.data.get('first_name'),
                last_name=request.data.get('last_name'),
                password="password123"
            )
            # Mise à jour du rôle dans le profil lié
            user.profile.role = request.data.get('role', 'LOCATAIRE')
            user.profile.save()
            
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
   

class UserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        data = request.data
        
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        
        if data.get('password'):
            user.set_password(data.get('password'))
            
        user.save()
        user.profile.role = data.get('role', user.profile.role)
        user.profile.save()
        
        return Response({'message': 'Utilisateur mis à jour'})

