-- Script SQL finale per completare il sistema coppa
-- Esegui questo script nell'SQL Editor del dashboard Supabase

-- Aggiungi solo la colonna group_letter alla tabella matches
ALTER TABLE matches 
ADD COLUMN group_letter VARCHAR(1) DEFAULT NULL;

-- Aggiungi un commento per documentare la colonna
COMMENT ON COLUMN matches.group_letter IS 'Lettera del girone per i tornei coppa (A, B, C, D)';

-- Verifica che la colonna sia stata aggiunta correttamente
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'matches' 
AND column_name = 'group_letter';
