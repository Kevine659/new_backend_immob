from django.urls import path,include
from .views import QuartierListView, QuartierDetailView, BienImmobilierDetailView, BienImmobilierListCreateView,ImageBienViewSet, ReservationViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'images-biens', ImageBienViewSet, basename='imagebien')
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('api/quartiers/', QuartierListView.as_view(), name='quartier-list'),
    path('api/quartiers/<int:pk>/', QuartierDetailView.as_view(), name='quartier-detail'),
    
    path('api/biens/', BienImmobilierListCreateView.as_view(), name='bien-list'),
    path('api/biens/<int:pk>/', BienImmobilierDetailView.as_view(), name='bien-detail'),
    path('api/', include(router.urls)),
    
]
