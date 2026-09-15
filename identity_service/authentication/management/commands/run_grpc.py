from django.core.management.base import BaseCommand
from authentication.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Identity Service gRPC server on port 50053'

    def handle(self, *args, **options):
        serve()
