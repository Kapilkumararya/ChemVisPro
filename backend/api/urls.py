from django.urls import path
from .views import EquipmentUploadView, register_user, login_user

urlpatterns = [
    path('upload/', EquipmentUploadView.as_view(), name='upload'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
]