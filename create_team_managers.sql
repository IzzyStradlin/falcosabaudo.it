-- GD (allenatore) per squadra e competizione, mostrato come tooltip in campionato.html
CREATE TABLE IF NOT EXISTS team_managers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competition_id UUID NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    gd_name TEXT NOT NULL,
    UNIQUE (competition_id, team_id)
);

-- Dati SUPERLEGA EUROPEA FALCO SABAUDO 2026/27 (nickname dal foglio Excel)
INSERT INTO team_managers (competition_id, team_id, gd_name)
SELECT '8309feef-c4fe-4f31-9616-ddd834b049dd', t.id, v.gd
FROM (VALUES
    ('AJAX', 'LolloDalla'),
    ('S. ETIENNE', 'Dandy-Ben'),
    ('ATHLETIC BILBAO', 'MRUEFA'),
    ('BOLOGNA', 'Nick 2565'),
    ('CAGLIARI', 'RomboDiTuono'),
    ('GENOA', 'Davtarus'),
    ('HIBERNIAN', 'Alex57'),
    ('IPSWICH TOWN', 'Islollo/Widah'),
    ('MAGONZA', 'Polpa'),
    ('MANCHESTER CITY', 'AleVigna'),
    ('MONACO', 'Fabrigranata'),
    ('PARTIZAN', 'Zoff'),
    ('PESCARA', 'Sarchia'),
    ('PISTOIESE', 'Bortop'),
    ('Q.P. RANGERS', 'Invernomuto'),
    ('REAL MADRID', 'Piper'),
    ('ROMA', 'Puliciccio'),
    ('SAMPDORIA', 'Visigoto'),
    ('TERNANA', 'Maraz'),
    ('TORINO', 'Erbstein'),
    ('UDINESE', 'LeRoiMichel'),
    ('UNIVERSITATEA CRALOVA', 'Kfonti')
) AS v(team_name, gd)
JOIN teams t ON upper(t.name) = v.team_name
JOIN team_competitions tc ON tc.team_id = t.id AND tc.competition_id = '8309feef-c4fe-4f31-9616-ddd834b049dd'
ON CONFLICT (competition_id, team_id) DO UPDATE SET gd_name = EXCLUDED.gd_name;

-- Controllo: deve restituire 22
SELECT count(*) FROM team_managers WHERE competition_id = '8309feef-c4fe-4f31-9616-ddd834b049dd';
