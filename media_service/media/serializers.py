import os
import json
from rest_framework import serializers
from .models import MediaFile

ALLOWED_EXTENSIONS = {
    'IMAGE': ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'],
    'DOCUMENT': ['.pdf', '.txt', '.doc', '.docx', '.csv', '.xlsx'],
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def parse_uuid_list(data, field_name):
    raw = data.get(field_name)
    if not raw:
        return []
    if isinstance(raw, str):
        raw = raw.strip()
        if raw.startswith('[') and raw.endswith(']'):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = [x.strip() for x in raw[1:-1].split(',') if x.strip()]
        else:
            raw = [x.strip() for x in raw.split(',') if x.strip()]
    if isinstance(raw, list):
        result = []
        for item in raw:
            if isinstance(item, list):
                for sub in item:
                    if sub:
                        result.append(str(sub).strip())
            elif item:
                result.append(str(item).strip())
        return result
    return []


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    visibility = serializers.ChoiceField(choices=MediaFile.VISIBILITY_CHOICES, default='PUBLIC')
    shared_with_users = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    shared_with_tenants = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        allowed = ALLOWED_EXTENSIONS['IMAGE'] + ALLOWED_EXTENSIONS['DOCUMENT']
        if ext not in allowed:
            raise serializers.ValidationError(f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(allowed)}")

        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(f"File size exceeds limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.")

        return value

    def to_internal_value(self, data):
        raw_dict = {}
        for k in data:
            raw_dict[k] = data[k]

        if 'visibility' in raw_dict and isinstance(raw_dict['visibility'], str):
            raw_dict['visibility'] = raw_dict['visibility'].upper()

        if 'shared_with_users' in data:
            if hasattr(data, 'getlist'):
                val = data.getlist('shared_with_users')
            else:
                val = data['shared_with_users']
            raw_dict['shared_with_users'] = parse_uuid_list({'shared_with_users': val}, 'shared_with_users')

        if 'shared_with_tenants' in data:
            if hasattr(data, 'getlist'):
                val = data.getlist('shared_with_tenants')
            else:
                val = data['shared_with_tenants']
            raw_dict['shared_with_tenants'] = parse_uuid_list({'shared_with_tenants': val}, 'shared_with_tenants')

        return super().to_internal_value(raw_dict)

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = [
            'id', 'tenant_id', 'uploaded_by', 'original_filename',
            'file_url', 'content_type', 'file_size', 'file_type',
            'visibility', 'shared_with_users', 'shared_with_tenants',
            'created_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'file_url', 'created_at']

class ShareMediaSerializer(serializers.Serializer):
    visibility = serializers.ChoiceField(choices=MediaFile.VISIBILITY_CHOICES)
    shared_with_users = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    shared_with_tenants = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def to_internal_value(self, data):
        raw_dict = {}
        for k in data:
            raw_dict[k] = data[k]

        if 'visibility' in raw_dict and isinstance(raw_dict['visibility'], str):
            raw_dict['visibility'] = raw_dict['visibility'].upper()

        if 'shared_with_users' in data:
            if hasattr(data, 'getlist'):
                val = data.getlist('shared_with_users')
            else:
                val = data['shared_with_users']
            raw_dict['shared_with_users'] = parse_uuid_list({'shared_with_users': val}, 'shared_with_users')

        if 'shared_with_tenants' in data:
            if hasattr(data, 'getlist'):
                val = data.getlist('shared_with_tenants')
            else:
                val = data['shared_with_tenants']
            raw_dict['shared_with_tenants'] = parse_uuid_list({'shared_with_tenants': val}, 'shared_with_tenants')

        return super().to_internal_value(raw_dict)


