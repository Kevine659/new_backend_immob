
from django.urls import path
from .views import GoogleLoginView, RegisterView,LoginView, UserListView, UserDetailView,UserProfileView

urlpatterns = [
    path('api/auth/google/', GoogleLoginView.as_view(), name='google_login_api'),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('api/profile/', UserProfileView.as_view(), name='user-profile'),
    
]

