from django.core.management.base import BaseCommand
from media.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Media Service gRPC server on port 50058'

    def handle(self, *args, **options):
        serve()
