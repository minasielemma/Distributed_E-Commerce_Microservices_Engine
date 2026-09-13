import os
from cryptography.hazmat.primitives import serialization
from key_utils import new_rsa_key, pem_key, self_signed_ca, signed_cert

KEYS_DIR = os.getenv("KEYS_DIR", "/shared_keys")
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "jwt_private.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "jwt_public.pem")

# gRPC mTLS paths
GRPC_CA_CERT_PATH = os.path.join(KEYS_DIR, "grpc_ca.crt")
GRPC_CA_KEY_PATH = os.path.join(KEYS_DIR, "grpc_ca.key")
GRPC_SERVER_CERT_PATH = os.path.join(KEYS_DIR, "grpc_server.crt")
GRPC_SERVER_KEY_PATH = os.path.join(KEYS_DIR, "grpc_server.key")
GRPC_CLIENT_CERT_PATH = os.path.join(KEYS_DIR, "grpc_client.crt")
GRPC_CLIENT_KEY_PATH = os.path.join(KEYS_DIR, "grpc_client.key")



def generate_rsa_keypair():
    os.makedirs(KEYS_DIR, exist_ok=True)

    if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
        private_key = new_rsa_key()
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(pem_key(private_key))
        public_key = private_key.public_key()
        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))


def generate_grpc_mtls_certs():
    os.makedirs(KEYS_DIR, exist_ok=True)

    if all(os.path.exists(p) for p in [
        GRPC_CA_CERT_PATH, GRPC_SERVER_CERT_PATH, GRPC_SERVER_KEY_PATH,
        GRPC_CLIENT_CERT_PATH, GRPC_CLIENT_KEY_PATH
    ]):
        return

    ca_key = new_rsa_key()
    ca_cert = self_signed_ca(ca_key)

    with open(GRPC_CA_KEY_PATH, "wb") as f:
        f.write(pem_key(ca_key))
    with open(GRPC_CA_CERT_PATH, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    server_key, server_cert = signed_cert("catalog_service", ca_key, ca_cert, is_server=True)
    with open(GRPC_SERVER_KEY_PATH, "wb") as f:
        f.write(pem_key(server_key))
    with open(GRPC_SERVER_CERT_PATH, "wb") as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))

    client_key, client_cert = signed_cert("order_service", ca_key, ca_cert)
    with open(GRPC_CLIENT_KEY_PATH, "wb") as f:
        f.write(pem_key(client_key))
    with open(GRPC_CLIENT_CERT_PATH, "wb") as f:
        f.write(client_cert.public_bytes(serialization.Encoding.PEM))

    print("[generate_keys] gRPC mTLS certificates generated.")


if __name__ == "__main__":
    generate_rsa_keypair()
    generate_grpc_mtls_certs()
