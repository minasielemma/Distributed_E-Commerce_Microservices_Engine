import os
import sys
import uuid
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "identity_project.settings")
django.setup()

from django.contrib.auth import get_user_model
from authentication.models import Notification, ActivityLog
from authentication.identity_pb2 import (
    UserData,
    UserLookupResponse,
    NotificationResponse,
    AuditLogResponse
)
from authentication.identity_pb2_grpc import IdentityServiceServicer, add_IdentityServiceServicer_to_server

User = get_user_model()
KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class IdentityServicer(IdentityServiceServicer):
    def LookupUsers(self, request, context):
        try:
            qs = User.objects.all()
            if request.user_id:
                qs = qs.filter(id=request.user_id)
            if request.tenant_id:
                qs = qs.filter(tenant_id=request.tenant_id)
            if request.role:
                qs = qs.filter(role=request.role)

            users_list = []
            for u in qs[:50]:
                users_list.append(UserData(
                    id=str(u.id),
                    email=u.email or "",
                    role=getattr(u, 'role', '') or '',
                    tenant_id=str(getattr(u, 'tenant_id', '') or ''),
                    first_name=u.first_name or "",
                    last_name=u.last_name or ""
                ))
            return UserLookupResponse(users=users_list)
        except Exception as e:
            print(f"[Identity gRPC] Error in LookupUsers: {str(e)}")
            return UserLookupResponse(users=[])

    def CreateInternalNotification(self, request, context):
        try:
            recipient_id = request.recipient_id
            user_obj = None
            if recipient_id:
                user_obj = User.objects.filter(id=recipient_id).first()

            notif = Notification.objects.create(
                user=user_obj,
                recipient_id=recipient_id or (str(user_obj.id) if user_obj else None),
                tenant_id=request.tenant_id or (str(getattr(user_obj, 'tenant_id', '')) if user_obj else None),
                title=request.title or "Internal Notification",
                message=request.message,
                notification_type=request.notification_type or "SYSTEM"
            )
            return NotificationResponse(success=True, notification_id=str(notif.id))
        except Exception as e:
            print(f"[Identity gRPC] Error in CreateInternalNotification: {str(e)}")
            return NotificationResponse(success=False, notification_id="")

    def CreateAuditLog(self, request, context):
        try:
            ActivityLog.objects.create(
                service_name=request.service_name or "system",
                action=request.action,
                user_id=request.user_id or None,
                tenant_id=request.tenant_id or None,
                details=request.details or ""
            )
            return AuditLogResponse(success=True)
        except Exception as e:
            print(f"[Identity gRPC] Error in CreateAuditLog: {str(e)}")
            return AuditLogResponse(success=False)


def serve():
    port = os.getenv("GRPC_PORT", "50053")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_IdentityServiceServicer_to_server(IdentityServicer(), server)

    server_cert_path = os.path.join(KEYS_DIR, "grpc_server.crt")
    server_key_path = os.path.join(KEYS_DIR, "grpc_server.key")
    ca_cert_path = os.path.join(KEYS_DIR, "grpc_ca.crt")

    if os.path.exists(server_cert_path) and os.path.exists(server_key_path) and os.path.exists(ca_cert_path):
        server_cert = open(server_cert_path, "rb").read()
        server_key = open(server_key_path, "rb").read()
        ca_cert = open(ca_cert_path, "rb").read()
        credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True,
        )
        server.add_secure_port(f"[::]:{port}", credentials)
        print(f"[Identity gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Identity gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
