from django.core.management.base import BaseCommand
from cart.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Cart Service gRPC server on port 50057'

    def handle(self, *args, **options):
        serve()
