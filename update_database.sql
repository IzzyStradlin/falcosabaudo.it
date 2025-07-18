-- Script SQL per aggiornare la struttura del database esistente
-- Questo script aggiorna le tabelle esistenti senza ricrearle

-- 1. Prima verifichiamo i tipi delle chiavi primarie
DO $$
DECLARE
    teams_id_type text;
    competitions_id_type text;
BEGIN
    -- Ottieni il tipo di teams.id
    SELECT data_type INTO teams_id_type
    FROM information_schema.columns 
    WHERE table_name = 'teams' AND column_name = 'id';
    
    -- Ottieni il tipo di competitions.id  
    SELECT data_type INTO competitions_id_type
    FROM information_schema.columns 
    WHERE table_name = 'competitions' AND column_name = 'id';
    
    RAISE NOTICE 'teams.id type: %, competitions.id type: %', teams_id_type, competitions_id_type;
END $$;

-- 2. Creiamo la tabella di collegamento con i tipi corretti
CREATE TABLE IF NOT EXISTS team_competitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  competition_id UUID REFERENCES competitions(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(team_id, competition_id)
);

-- 3. Se esiste la colonna competition_id nella tabella teams, migriamo i dati
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'teams' AND column_name = 'competition_id') THEN
        
        -- Migra i dati esistenti nella tabella di collegamento
        INSERT INTO team_competitions (team_id, competition_id)
        SELECT id, competition_id 
        FROM teams 
        WHERE competition_id IS NOT NULL
        ON CONFLICT (team_id, competition_id) DO NOTHING;
        
        -- Rimuovi la colonna competition_id dalla tabella teams
        ALTER TABLE teams DROP COLUMN IF EXISTS competition_id;
        
        RAISE NOTICE 'Dati migrati e colonna competition_id rimossa da teams';
    ELSE
        RAISE NOTICE 'Colonna competition_id non trovata in teams, struttura già corretta';
    END IF;
END $$;

-- 4. Assicuriamoci che le tabelle abbiano i campi necessari
ALTER TABLE teams ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE competitions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- 5. Verifica della struttura finale
SELECT 'teams' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'teams' 
ORDER BY ordinal_position;

SELECT 'competitions' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'competitions' 
ORDER BY ordinal_position;

SELECT 'team_competitions' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'team_competitions' 
ORDER BY ordinal_position;
