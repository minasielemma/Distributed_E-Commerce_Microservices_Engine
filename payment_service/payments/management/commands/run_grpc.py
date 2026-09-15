from django.core.management.base import BaseCommand
from payments.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Payment Service gRPC server on port 50055'

    def handle(self, *args, **options):
        serve()
