-- Script per verificare lo stato delle tabelle nel database
-- Esegui questo per vedere quali tabelle esistono e la loro struttura

-- Controlla se esistono le tabelle base
SELECT 
    'competitions' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'competitions') 
         THEN 'EXISTS' 
         ELSE 'NOT EXISTS' 
    END as status
UNION ALL
SELECT 
    'teams' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'teams') 
         THEN 'EXISTS' 
         ELSE 'NOT EXISTS' 
    END as status
UNION ALL
SELECT 
    'team_competitions' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'team_competitions') 
         THEN 'EXISTS' 
         ELSE 'NOT EXISTS' 
    END as status
UNION ALL
SELECT 
    'matchdays' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'matchdays') 
         THEN 'EXISTS' 
         ELSE 'NOT EXISTS' 
    END as status
UNION ALL
SELECT 
    'matches' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'matches') 
         THEN 'EXISTS' 
         ELSE 'NOT EXISTS' 
    END as status
UNION ALL
SELECT 
    'standings' as table_name,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'standings') 
         THEN 'EXISTS' 
         ELSE 'NOT EXISTS' 
    END as status
ORDER BY table_name;

-- Mostra la struttura della tabella matches se esiste
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'matches' 
ORDER BY ordinal_position;
