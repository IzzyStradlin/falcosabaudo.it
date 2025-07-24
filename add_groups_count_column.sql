-- Script SQL per aggiungere la colonna groups_count alla tabella competitions
-- Esegui questo script nell'SQL Editor del dashboard Supabase

-- Aggiungi la colonna groups_count alla tabella competitions
ALTER TABLE competitions 
ADD COLUMN groups_count INTEGER DEFAULT NULL;

-- Aggiungi un commento per documentare la colonna
COMMENT ON COLUMN competitions.groups_count IS 'Numero di gironi per i tornei di tipo coppa (2 o 4)';

-- Opzionale: aggiungi un constraint per validare i valori (solo 2 o 4 gironi)
ALTER TABLE competitions 
ADD CONSTRAINT check_groups_count 
CHECK (groups_count IS NULL OR groups_count IN (2, 4));

-- Verifica che la colonna sia stata aggiunta correttamente
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'competitions' 
AND column_name = 'groups_count';
