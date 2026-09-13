from django.urls import path
from .views import FileUploadView, MediaFileDetailView, MediaFileListView, ShareMediaView, MediaFileDownloadView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='media_upload'),
    path('files/', MediaFileListView.as_view(), name='media_list'),
    path('files/<uuid:pk>/', MediaFileDetailView.as_view(), name='media_detail'),
    path('files/<uuid:pk>/download/', MediaFileDownloadView.as_view(), name='media_download'),
    path('files/<uuid:pk>/share/', ShareMediaView.as_view(), name='media_share'),
]

