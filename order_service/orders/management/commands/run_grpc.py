from django.core.management.base import BaseCommand
from orders.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Order Service gRPC server on port 50054'

    def handle(self, *args, **options):
        serve()
