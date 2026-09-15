from django.core.management.base import BaseCommand
from inventory.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Inventory Service gRPC server on port 50052'

    def handle(self, *args, **options):
        serve()
