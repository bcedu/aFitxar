import sqlite3
from datetime import datetime
import django
import os
import sys


# Connexió a les bases de dades V1 i V2
conn_v1 = sqlite3.connect('db_v1.sqlite3')
conn_v2 = sqlite3.connect('db.sqlite3')


def migrar_treballadors():
    cursor_v1 = conn_v1.cursor()
    cursor_v2 = conn_v2.cursor()

    # Selecciona tots els treballadors de V1
    cursor_v1.execute("SELECT id, nom, vat, codi_entrada FROM marcatge_treballador")
    treballadors = cursor_v1.fetchall()

    # Inserció de treballadors a V2 amb jornada_diaria per defecte (8.0 hores)
    for treballador in treballadors:
        cursor_v2.execute("""
            INSERT INTO marcatge_treballador (id, nom, vat, codi_entrada, jornada_diaria, ajustar_jornada_diaria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (treballador[0], treballador[1], treballador[2], treballador[3], 0.0, True))

    conn_v2.commit()
    print("Migració de treballadors completada.")


def migrar_marcatges():
    cursor_v1 = conn_v1.cursor()
    cursor_v2 = conn_v2.cursor()

    # Selecciona tots els marcatges de V1
    cursor_v1.execute("SELECT id, entrada, sortida, treballador_id FROM marcatge_marcatge")
    marcatges = cursor_v1.fetchall()

    marcatge_dia = {}

    for marcatge in marcatges:
        id, entrada, sortida, treballador_id = marcatge

        # Inserir marcatge d'entrada
        cursor_v2.execute("""
            INSERT INTO marcatge_marcatge (data, tipus, treballador_id)
            VALUES (?, ?, ?)
        """, (entrada, "entrada", treballador_id))

        # Inserir marcatge de sortida
        if sortida:
            cursor_v2.execute("""
                INSERT INTO marcatge_marcatge (data, tipus, treballador_id)
                VALUES (?, ?, ?)
            """, (sortida, "sortida", treballador_id))

    # emplenem el diatreball dels marcatges
    cursor_v2.execute('SELECT id, data, treballador_id FROM marcatge_marcatge')
    marcatges = cursor_v2.fetchall()
    for marcatge in marcatges:
        marcatge_id, entrada, treballador_id = marcatge
        cursor_v2.execute('SELECT id, dia FROM marcatge_diatreball WHERE treballador_id = ? AND dia = ?', (treballador_id, entrada.split(' ')[0]))
        diatreball = cursor_v2.fetchone()
        if not diatreball:
            cursor_v2.execute("""
                INSERT INTO marcatge_diatreball (dia, treballador_id, hores_totals, hores_restants)
                VALUES (?, ?, 0, 0)
            """, (entrada.split(' ')[0], treballador_id))
            cursor_v2.execute('SELECT id, dia FROM marcatge_diatreball WHERE treballador_id = ? AND dia = ?', (treballador_id, entrada.split(' ')[0]))
            diatreball = cursor_v2.fetchone()
        if diatreball:
            dia_treball_id = diatreball[0]
            cursor_v2.execute('UPDATE marcatge_marcatge SET dia_treball_id = ? WHERE id = ?', (dia_treball_id, marcatge_id))
        else:
            raise Exception("Error", "No s'ha torbat dia de treball per el marcatge")

    conn_v2.commit()
    print("Migració de marcatges completada.")


# Executa la migració
migrar_treballadors()
migrar_marcatges()

# Tanca les connexions
conn_v1.close()
conn_v2.close()

# Calculem camps funcio
# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PortalMarcatge.settings')
django.setup()
from marcatge.models import Treballador
from tqdm import tqdm
for t in tqdm(Treballador.objects.filter()):
    t.jornada_diaria = 6
    t.save()

print("Migració completada amb èxit.")
