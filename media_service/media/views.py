import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse, FileResponse, Http404
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MediaFile
from .serializers import FileUploadSerializer, MediaFileSerializer, ShareMediaSerializer, ALLOWED_EXTENSIONS
from common.filters import GeneralFilter

class FileUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data['file']
        visibility = serializer.validated_data.get('visibility', 'PUBLIC')
        shared_users = [str(u) for u in serializer.validated_data.get('shared_with_users', [])]
        shared_tenants = [str(t) for t in serializer.validated_data.get('shared_with_tenants', [])]

        original_filename = file_obj.name
        ext = os.path.splitext(original_filename)[1].lower()
        file_id = uuid.uuid4()
        secure_filename = f"{file_id}{ext}"
        storage_path = os.path.join('uploads', secure_filename)

        full_path = default_storage.save(storage_path, file_obj)
        file_url = f"/api/media/files/{file_id}/download/"

        file_type = 'IMAGE' if ext in ALLOWED_EXTENSIONS['IMAGE'] else 'DOCUMENT'
        user_id = str(request.user.id) if request.user and request.user.is_authenticated else None
        tenant_id = getattr(request.user, 'tenant_id', None)

        media_file = MediaFile.objects.create(
            id=file_id,
            tenant_id=tenant_id,
            uploaded_by=user_id,
            original_filename=original_filename,
            file_url=file_url,
            storage_path=full_path,
            content_type=getattr(file_obj, 'content_type', 'application/octet-stream'),
            file_size=file_obj.size,
            file_type=file_type,
            visibility=visibility,
            shared_with_users=shared_users,
            shared_with_tenants=shared_tenants
        )

        return Response({
            'message': 'File uploaded successfully',
            'file_id': str(media_file.id),
            'file_url': media_file.file_url,
            'original_filename': media_file.original_filename,
            'content_type': media_file.content_type,
            'file_size': media_file.file_size,
            'file_type': media_file.file_type,
            'visibility': media_file.visibility
        }, status=status.HTTP_201_CREATED)

class MediaFileDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            media_file = MediaFile.objects.get(pk=pk)
        except MediaFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        if not media_file.has_access(request.user):
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'error': 'Access denied to this file'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MediaFileSerializer(media_file)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            media_file = MediaFile.objects.get(pk=pk)
        except MediaFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        user_id_str = str(request.user.id)
        role = (getattr(request.user, 'role', '') or '').upper()
        is_admin = role == 'ADMIN' or getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)

        if str(media_file.uploaded_by) != user_id_str and not is_admin:
            return Response({'error': 'Only owner or admin can delete this file'}, status=status.HTTP_403_FORBIDDEN)

        if default_storage.exists(media_file.storage_path):
            default_storage.delete(media_file.storage_path)

        media_file.delete()
        return Response({'message': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class MediaFileDownloadView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            media_file = MediaFile.objects.get(pk=pk)
        except MediaFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        # Allow access if visibility is PUBLIC, or if user satisfies has_access check
        is_public = (media_file.visibility == 'PUBLIC')
        if not is_public and not media_file.has_access(request.user):
            if not request.user or not request.user.is_authenticated:
                return Response({'error': 'Authentication required to download this file'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'error': 'Access denied to this file'}, status=status.HTTP_403_FORBIDDEN)


        if not default_storage.exists(media_file.storage_path):
            return Response({'error': 'File content not found on server storage'}, status=status.HTTP_404_NOT_FOUND)

        file_handle = default_storage.open(media_file.storage_path, 'rb')
        response = FileResponse(file_handle, content_type=media_file.content_type)
        response['Content-Disposition'] = f'inline; filename="{media_file.original_filename}"'
        return response

class ShareMediaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            media_file = MediaFile.objects.get(pk=pk)
        except MediaFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        user_id_str = str(request.user.id)
        role = (getattr(request.user, 'role', '') or '').upper()
        is_admin = role == 'ADMIN' or getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)

        if media_file.uploaded_by and str(media_file.uploaded_by) != user_id_str and not is_admin and user_id_str not in [str(u) for u in (media_file.shared_with_users or [])]:
            return Response({'error': 'Only file owner, participant, or admin can change sharing settings'}, status=status.HTTP_403_FORBIDDEN)


        serializer = ShareMediaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        media_file.visibility = serializer.validated_data['visibility']
        media_file.shared_with_users = [str(u) for u in serializer.validated_data.get('shared_with_users', [])]
        media_file.shared_with_tenants = [str(t) for t in serializer.validated_data.get('shared_with_tenants', [])]
        media_file.save()

        return Response({
            'message': 'Sharing permissions updated successfully',
            'file_id': str(media_file.id),
            'visibility': media_file.visibility,
            'shared_with_users': media_file.shared_with_users,
            'shared_with_tenants': media_file.shared_with_tenants
        }, status=status.HTTP_200_OK)

class MediaFileListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = MediaFileSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return MediaFile.objects.filter(visibility='PUBLIC')

        user_id_str = str(user.id)
        tenant_id_str = str(getattr(user, 'tenant_id', ''))
        role = (getattr(user, 'role', '') or '').upper()
        is_admin = role == 'ADMIN' or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)

        if is_admin:
            qs = MediaFile.objects.all()
        else:
            from django.db.models import Q
            qs = MediaFile.objects.filter(
                Q(visibility='PUBLIC') |
                Q(uploaded_by=user_id_str) |
                Q(visibility='SHARED', shared_with_users__contains=user_id_str) |
                (Q(visibility='SHARED', shared_with_tenants__contains=tenant_id_str) if tenant_id_str else Q())
            )

        return GeneralFilter.apply_filters(qs, self.request, search_fields=['original_filename'])

