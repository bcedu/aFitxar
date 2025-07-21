#!/bin/bash

# Directori d'origen i de destinació
ORIGEN="/.../aFitxar/db.sqlite3"
DESTI="/.../aFitxar/backups"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
NOM_BACKUP="db_backup_$TIMESTAMP.sqlite3"
cp "$ORIGEN" "$DESTI/$NOM_BACKUP"

# Eliminar backups de fa més de 60 dies
find "$DESTI" -name "db_backup_*.sqlite3" -type f -mtime +60 -exec rm -f {} \;
