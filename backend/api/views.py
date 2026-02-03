import pandas as pd
import os
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import EquipmentDataset
from .serializers import UserSerializer

# --- Auth Views ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.username}, status=200)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.username}, status=200)
    return Response({'error': 'Invalid Credentials'}, status=401)

# --- Equipment Views ---

class EquipmentHistoryDetailView(APIView):
    # Only logged in users can access
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Fetch a specific history item. Ensures user owns it."""
        # This line ensures User A cannot see User B's file
        dataset = get_object_or_404(EquipmentDataset, pk=pk, user=request.user)
        
        file_path = os.path.join(settings.MEDIA_ROOT, dataset.file_name)
        
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            # Fallback if file was deleted but DB record exists
            return Response({"error": "File missing from server"}, status=500)

        # Re-run Analysis Logic on load
        def check_health(row):
            p = row.get('Pressure', 0)
            t = row.get('Temperature', 0)
            if p > 800 and t > 300: return 'CRITICAL'
            elif p > 600: return 'WARNING'
            return 'OK'

        if 'Pressure' in df.columns and 'Temperature' in df.columns:
            df['Status'] = df.apply(check_health, axis=1)
        else:
            df['Status'] = 'UNKNOWN'

        return Response({
            "stats": dataset.summary_stats,
            "data": df.fillna('').to_dict(orient='records'),
            "history_id": dataset.id
        })

class EquipmentUploadView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated] # CRITICAL: Enforces 403 if not logged in

    def get(self, request):
        """Fetch history list ONLY for the current user."""
        # Filter: user=request.user
        history = EquipmentDataset.objects.filter(user=request.user).order_by('-uploaded_at')[:5]
        return Response({
            "history": list(history.values('id', 'file_name', 'uploaded_at', 'total_records'))
        })

    def post(self, request):
        try:
            file_obj = request.FILES['file']
        except KeyError:
            return Response({"error": "No file provided"}, status=400)

        file_name = default_storage.save(file_obj.name, file_obj)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return Response({"error": f"Invalid CSV format: {str(e)}"}, status=400)

        # Analysis Logic
        def check_health(row):
            p = row.get('Pressure', 0)
            t = row.get('Temperature', 0)
            if p > 800 and t > 300: return 'CRITICAL'
            elif p > 600: return 'WARNING'
            return 'OK'

        if 'Pressure' in df.columns and 'Temperature' in df.columns:
            df['Status'] = df.apply(check_health, axis=1)
        else:
            df['Status'] = 'UNKNOWN'

        stats = {
            "total_count": int(len(df)),
            "avg_pressure": round(df['Pressure'].mean(), 2) if 'Pressure' in df else 0,
            "avg_temp": round(df['Temperature'].mean(), 2) if 'Temperature' in df else 0,
            "type_distribution": df['Type'].value_counts().to_dict() if 'Type' in df else {}
        }

        # SAVE: Attach the logged-in user to this record
        EquipmentDataset.objects.create(
            user=request.user,
            file_name=file_name,
            total_records=stats['total_count'],
            summary_stats=stats
        )
        
        # CLEANUP: Keep only last 5 for THIS user
        ids_to_keep = EquipmentDataset.objects.filter(user=request.user).order_by('-uploaded_at')[:5].values_list('id', flat=True)
        EquipmentDataset.objects.filter(user=request.user).exclude(id__in=ids_to_keep).delete()

        # RETURN: Updated history for THIS user
        history = EquipmentDataset.objects.filter(user=request.user).order_by('-uploaded_at')[:5]

        return Response({
            "stats": stats,
            "data": df.fillna('').to_dict(orient='records'),
            "history": list(history.values('id', 'file_name', 'uploaded_at', 'total_records'))
        })