import django
import os
import sys

# Configura l'entorn de Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PortalMarcatge.settings')
django.setup()

# Importa el model i executa la funció
from marcatge.models import Treballador

if __name__ == "__main__":
    print("Iniciant ajustament d'hores per tots els treballadors...")
    Treballador.cron_ajustar_hores()
    print("Procés complet!")
