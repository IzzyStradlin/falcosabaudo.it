-- Script SQL completo per completare il sistema coppa
-- Esegui questo script nell'SQL Editor del dashboard Supabase

-- 1. Aggiungi la colonna group_letter alla tabella matches (se non esiste già)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'matches' AND column_name = 'group_letter'
    ) THEN
        ALTER TABLE matches ADD COLUMN group_letter VARCHAR(1) DEFAULT NULL;
        COMMENT ON COLUMN matches.group_letter IS 'Lettera del girone per i tornei coppa (A, B, C, D)';
    END IF;
END $$;

-- 2. Aggiungi la colonna description alla tabella matchdays (se non esiste già)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'matchdays' AND column_name = 'description'
    ) THEN
        ALTER TABLE matchdays ADD COLUMN description TEXT DEFAULT NULL;
        COMMENT ON COLUMN matchdays.description IS 'Descrizione della giornata (es. "Andata Giornata 1", "Semifinali", ecc.)';
    END IF;
END $$;

-- 3. Verifica che tutte le colonne siano state aggiunte correttamente
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable, 
    column_default 
FROM information_schema.columns 
WHERE (table_name = 'competitions' AND column_name = 'groups_count')
   OR (table_name = 'matchdays' AND column_name = 'description')
   OR (table_name = 'matches' AND column_name = 'group_letter')
ORDER BY table_name, column_name;
