#!/bin/bash
rm db.sqlite3
./setup.sh
python migracio_v1_v2/migrar_dades.py

