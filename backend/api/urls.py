from django.urls import path
from .views import EquipmentUploadView, EquipmentHistoryDetailView, register_user, login_user

urlpatterns = [
    path('upload/', EquipmentUploadView.as_view(), name='upload'),
    path('history/<int:pk>/', EquipmentHistoryDetailView.as_view(), name='history_detail'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
]