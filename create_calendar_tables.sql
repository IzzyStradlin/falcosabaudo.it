-- Script SQL semplificato per creare solo le tabelle del calendario
-- Usa questo se hai già le tabelle competitions, teams, team_competitions

-- Aggiunta colonna is_active per campionati esistenti (se non esiste già)
ALTER TABLE competitions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Elimina le tabelle esistenti per ricrearle correttamente
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS matchdays CASCADE;
DROP TABLE IF EXISTS standings CASCADE;

-- Tabella per le giornate
CREATE TABLE matchdays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competition_id UUID REFERENCES competitions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(competition_id, round_number)
);

-- Tabella per le partite
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matchday_id UUID REFERENCES matchdays(id) ON DELETE CASCADE,
    home_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    home_score INTEGER,
    away_score INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    played_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(matchday_id, home_team_id, away_team_id)
);

-- Tabella per la classifica
CREATE TABLE standings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    competition_id UUID REFERENCES competitions(id) ON DELETE CASCADE,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team_id, competition_id)
);

-- Indici per migliorare le performance
CREATE INDEX idx_matchdays_competition_id ON matchdays(competition_id);
CREATE INDEX idx_matches_matchday_id ON matches(matchday_id);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX idx_standings_competition_id ON standings(competition_id);
CREATE INDEX idx_standings_points ON standings(points DESC, goal_difference DESC);

-- Trigger per aggiornare updated_at nella tabella standings
CREATE OR REPLACE FUNCTION update_standings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_standings_updated_at_trigger
    BEFORE UPDATE ON standings
    FOR EACH ROW
    EXECUTE FUNCTION update_standings_updated_at();

-- Funzione per calcolare la differenza reti
CREATE OR REPLACE FUNCTION calculate_goal_difference()
RETURNS TRIGGER AS $$
BEGIN
    NEW.goal_difference = NEW.goals_for - NEW.goals_against;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_goal_difference_trigger
    BEFORE INSERT OR UPDATE ON standings
    FOR EACH ROW
    EXECUTE FUNCTION calculate_goal_difference();

-- Politiche RLS (Row Level Security)
ALTER TABLE matchdays ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE standings ENABLE ROW LEVEL SECURITY;

-- Politiche per permettere lettura a tutti e scrittura agli autenticati
CREATE POLICY "Anyone can view matchdays" ON matchdays FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage matchdays" ON matchdays FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Anyone can view matches" ON matches FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage matches" ON matches FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Anyone can view standings" ON standings FOR SELECT USING (true);
CREATE POLICY "Authenticated users can manage standings" ON standings FOR ALL USING (auth.role() = 'authenticated');

-- Messaggio di conferma
SELECT 'Tabelle per calendario e classifica create con successo!' as message;
