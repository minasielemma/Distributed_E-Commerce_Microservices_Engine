import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes


def new_rsa_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def pem_key(key):
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )


def self_signed_ca(key):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "microservices-ca")])
    now = datetime.datetime.utcnow()
    return (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )


def signed_cert(cn, ca_key, ca_cert, is_server=False):
    key = new_rsa_key()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.utcnow()
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=3650))
    )
    if is_server:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(cn), x509.DNSName("catalog_service")]),
            critical=False
        )
    return key, builder.sign(ca_key, hashes.SHA256())
