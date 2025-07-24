# Istruzioni per completare il sistema Coppa

## Passo 1: Accedi al Dashboard Supabase
1. Vai su https://supabase.com/
2. Fai login con le tue credenziali
3. Seleziona il progetto del Falco Sabaudo

## Passo 2: Apri l'SQL Editor
1. Nel menu laterale, clicca su "SQL Editor"
2. Clicca su "New query" per creare una nuova query

## Passo 3: Esegui questo script SQL completo
Copia e incolla questo script nell'editor SQL e clicca "Run":

```sql
-- Script SQL completo per completare il sistema coppa
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
```

## Passo 4: Verifica il risultato
Esegui questa query per verificare:

```sql
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
```

## Passo 5: Testa il nuovo sistema Coppa
Una volta eseguito lo script, il sistema supporterà:

### ✅ **Fase Gironi Unificata**
- Giornata 1: Partite di TUTTI i gironi contemporaneamente
- Visualizzazione separata per ogni girone (A, B, C, D)
- Calendario chiaro e organizzato

### ✅ **Fase Finale Strutturata**
- **2 Gironi**: Finale + Finale 3° posto
- **4 Gironi**: Semifinali + Finale + Finale 3° posto
- Struttura pronta per tabellone eliminazione

### ✅ **Database Ottimizzato**
- `competitions.groups_count`: Numero di gironi (2 o 4)
- `matchdays.description`: Descrizione giornate ("Andata Giornata 1", "Semifinali")
- `matches.group_letter`: Identificazione girone (A, B, C, D)

Il sistema è ora pronto per gestire tornei coppa professionali! 🏆
