from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Asigna el rol SUPERUSUARIO al usuario con username "faq"'

    def handle(self, *args, **kwargs):
        try:
            user = CustomUser.objects.get(username='faq')
            user.rol = 'SUPERUSUARIO'
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS('El usuario "faq" ha sido asignado al rol SUPERUSUARIO correctamente.'))
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('El usuario "faq" no existe.'))
