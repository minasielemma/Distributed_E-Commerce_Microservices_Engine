import os
import grpc
from chat.identity_pb2 import (
    UserLookupRequest,
    NotificationRequest
)
from chat.identity_pb2_grpc import IdentityServiceStub
from chat.order_pb2 import GetOrderRequest
from chat.order_pb2_grpc import OrderServiceStub
from chat.media_pb2 import GetMediaRequest
from chat.media_pb2_grpc import MediaServiceStub

IDENTITY_GRPC_HOST = os.getenv('IDENTITY_GRPC_HOST', 'identity_service:50053')
ORDER_GRPC_HOST = os.getenv('ORDER_GRPC_HOST', 'order_service:50054')
MEDIA_GRPC_HOST = os.getenv('MEDIA_GRPC_HOST', 'media_service:50058')
KEYS_DIR = os.getenv('KEYS_DIR', '/shared_keys')


def _get_channel_credentials():
    ca_path = os.path.join(KEYS_DIR, 'grpc_ca.crt')
    client_cert_path = os.path.join(KEYS_DIR, 'grpc_client.crt')
    client_key_path = os.path.join(KEYS_DIR, 'grpc_client.key')

    if os.path.exists(ca_path) and os.path.exists(client_cert_path) and os.path.exists(client_key_path):
        ca_cert = open(ca_path, 'rb').read()
        client_cert = open(client_cert_path, 'rb').read()
        client_key = open(client_key_path, 'rb').read()
        return grpc.ssl_channel_credentials(
            root_certificates=ca_cert,
            private_key=client_key,
            certificate_chain=client_cert,
        )
    return None


def _get_channel(host):
    creds = _get_channel_credentials()
    if creds:
        target_name = host.split(':')[0].replace('-', '_')
        options = [('grpc.ssl_target_name_override', target_name)]
        return grpc.secure_channel(host, creds, options=options)
    return grpc.insecure_channel(host)


def lookup_users_grpc(user_id="", tenant_id="", role=""):
    try:
        channel = _get_channel(IDENTITY_GRPC_HOST)
        stub = IdentityServiceStub(channel)
        response = stub.LookupUsers(UserLookupRequest(
            user_id=str(user_id or ""),
            tenant_id=str(tenant_id or ""),
            role=str(role or "")
        ), timeout=5)
        return response.users
    except Exception as e:
        print(f"[Chat Service] gRPC error in LookupUsers: {e}")
        return []


def send_notification_grpc(recipient_id="", tenant_id="", title="", message="", notification_type="CHAT"):
    try:
        channel = _get_channel(IDENTITY_GRPC_HOST)
        stub = IdentityServiceStub(channel)
        response = stub.CreateInternalNotification(NotificationRequest(
            recipient_id=str(recipient_id or ""),
            tenant_id=str(tenant_id or ""),
            title=title,
            message=message,
            notification_type=notification_type
        ), timeout=5)
        return response
    except Exception as e:
        print(f"[Chat Service] gRPC error in CreateInternalNotification: {e}")
        return None


def get_order_grpc(order_id_str):
    try:
        channel = _get_channel(ORDER_GRPC_HOST)
        stub = OrderServiceStub(channel)
        response = stub.GetOrder(GetOrderRequest(order_id=str(order_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Chat Service] gRPC error in GetOrder: {e}")
        return None


def get_media_grpc(media_id_str):
    try:
        channel = _get_channel(MEDIA_GRPC_HOST)
        stub = MediaServiceStub(channel)
        response = stub.GetMedia(GetMediaRequest(media_id=str(media_id_str)), timeout=5)
        return response
    except Exception as e:
        print(f"[Chat Service] gRPC error in GetMedia: {e}")
        return None
