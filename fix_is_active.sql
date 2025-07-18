-- Script per aggiungere la colonna is_active se non esiste
-- Eseguire questo script in Supabase SQL Editor

-- Aggiunge la colonna is_active se non esiste già
ALTER TABLE competitions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Aggiorna tutti i campionati esistenti per essere attivi
UPDATE competitions SET is_active = TRUE WHERE is_active IS NULL;

-- Verifica che la colonna sia stata aggiunta
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'competitions' AND column_name = 'is_active';
