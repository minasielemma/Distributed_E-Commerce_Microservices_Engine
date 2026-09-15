import os
import sys
import uuid
import concurrent.futures
import grpc
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "media_project.settings")
django.setup()

from media.models import MediaFile
from media.media_pb2 import (
    GetMediaResponse
)
from media.media_pb2_grpc import MediaServiceServicer, add_MediaServiceServicer_to_server

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")


class MediaServicer(MediaServiceServicer):
    def GetMedia(self, request, context):
        media_id_str = request.media_id
        try:
            mid = uuid.UUID(media_id_str)
            asset = MediaFile.objects.get(id=mid)
            return GetMediaResponse(
                media_id=str(asset.id),
                url=asset.file_url if asset.file_url else "",
                file_name=getattr(asset, 'original_filename', '') or "",
                content_type=getattr(asset, 'content_type', '') or "",
                size=getattr(asset, 'file_size', 0) or 0,
                found=True,
                error_message=""
            )
        except MediaFile.DoesNotExist:
            return GetMediaResponse(media_id=media_id_str, url="", file_name="", content_type="", size=0, found=False, error_message="Media asset not found")
        except Exception as e:
            return GetMediaResponse(media_id=media_id_str, url="", file_name="", content_type="", size=0, found=False, error_message=str(e))


def serve():
    port = os.getenv("GRPC_PORT", "50058")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    add_MediaServiceServicer_to_server(MediaServicer(), server)

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
        print(f"[Media gRPC Server] Running on port {port} with mTLS...")
    else:
        server.add_insecure_port(f"[::]:{port}")
        print(f"[Media gRPC Server] Running on port {port} (insecure fallback)...")

    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
