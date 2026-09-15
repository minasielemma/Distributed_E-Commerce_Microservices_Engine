from django.core.management.base import BaseCommand
from finance.grpc_server import serve

class Command(BaseCommand):
    help = 'Starts the Finance Service gRPC server on port 50056'

    def handle(self, *args, **options):
        serve()
