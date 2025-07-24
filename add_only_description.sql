-- Script SQL per aggiungere solo la colonna description (groups_count già esiste)
-- Esegui questo script nell'SQL Editor del dashboard Supabase

-- Aggiungi la colonna description alla tabella matchdays
ALTER TABLE matchdays 
ADD COLUMN description TEXT DEFAULT NULL;

-- Aggiungi un commento per documentare la colonna
COMMENT ON COLUMN matchdays.description IS 'Descrizione della giornata (es. "Girone A - Andata Giornata 1", "Semifinali", ecc.)';

-- Verifica che la colonna sia stata aggiunta correttamente
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'matchdays' 
AND column_name = 'description';
