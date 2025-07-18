// Inizializzazione Supabase con retry
(async function initializeSupabase() {
    console.log('🚀 Inizializzazione Supabase...');
    
    // Aspetta che la libreria Supabase sia caricata
    let attempts = 0;
    while (!window.supabase && attempts < 100) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }
    
    if (!window.supabase) {
        console.error('❌ Errore: libreria Supabase non caricata dopo 10 secondi');
        return;
    }
    
    console.log('✅ Supabase libreria caricata');

    try {
        const supabaseUrl = 'https://hvviecqurdbpxxfmaapb.supabase.co';
        const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2dmllY3F1cmRicHh4Zm1hYXBiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIxMzMzMTEsImV4cCI6MjA2NzcwOTMxMX0.mGltlAbMzOSb6H2OVEDa4ukUpppEqqjtdKiSGKfjso4';
        window.supabaseClient = window.supabase.createClient(supabaseUrl, supabaseKey);
        console.log('✅ Client Supabase inizializzato:', window.supabaseClient);
        
        // Test di connessione
        const { data, error } = await window.supabaseClient.auth.getUser();
        if (error && error.message !== 'Auth session missing!') {
            console.warn('⚠️ Warning connessione Supabase:', error.message);
        } else {
            console.log('✅ Connessione Supabase OK');
        }
        
    } catch (error) {
        console.error('❌ Errore inizializzazione Supabase:', error);
    }
})();

// Gestione Autenticazione
window.AuthManager = class AuthManager {
    static async login(email, password) {
        console.log('🔐 AuthManager.login chiamato con:', email);
        
        if (!window.supabaseClient) {
            console.error('❌ supabaseClient non disponibile');
            throw new Error('Supabase non inizializzato');
        }
        
        try {
            console.log('📡 Chiamata signInWithPassword...');
            const { data, error } = await window.supabaseClient.auth.signInWithPassword({ 
                email: email.trim(), 
                password: password 
            });
            
            if (error) {
                console.error('❌ Errore di login:', error);
                throw new Error(error.message);
            }
            
            console.log('✅ Login riuscito:', data);
            return data;
        } catch (error) {
            console.error('❌ Errore durante il login:', error);
            throw error;
        }
    }

    static async logout() {
        try {
            const { error } = await window.supabaseClient.auth.signOut();
            if (error) {
                console.error('Errore di logout:', error.message);
                throw new Error(error.message);
            }
            console.log('Logout effettuato'); // Debug
        } catch (error) {
            console.error('Errore durante il logout:', error.message);
            throw error;
        }
    }

    static async getCurrentUser() {
        try {
            const { data: { session }, error } = await window.supabaseClient.auth.getSession();
            if (error) {
                console.error('Errore nel recupero della sessione:', error.message);
                throw new Error(error.message);
            }
            console.log('Sessione utente:', session); // Debug
            return session?.user;
        } catch (error) {
            console.error('Errore nel recupero dell\'utente corrente:', error.message);
            throw error;
        }
    }
}

// Gestione Squadre
window.TeamManager = class TeamManager {
    static async createTeam(name, competitionId = null) {
        // Prima creiamo la squadra senza competition_id
        const { data, error } = await window.supabaseClient
            .from('teams')
            .insert([{ name }])
            .select()
            .single();
        if (error) throw error;
        console.log('Squadra creata:', data); // Debug
        
        // Se c'è un competitionId, creiamo il collegamento
        if (competitionId) {
            await this.linkTeamToCompetition(data.id, competitionId);
        }
        
        return data;
    }

    static async linkTeamToCompetition(teamId, competitionId) {
        const { data, error } = await window.supabaseClient
            .from('team_competitions')
            .insert([{ team_id: teamId, competition_id: competitionId }])
            .select()
            .single();
        if (error) throw error;
        console.log('Team collegato al campionato:', data); // Debug
        return data;
    }

    static async addTeam(name) {
        return this.createTeam(name);
    }

    static async getAllTeams() {
        const { data, error } = await window.supabaseClient
            .from('teams')
            .select('*')
            .order('name');
        if (error) throw error;
        console.log('Squadre caricate:', data); // Debug
        return data;
    }

    static async getTeamsByCompetition(competitionId) {
        const { data, error } = await window.supabaseClient
            .from('team_competitions')
            .select(`
                team_id,
                teams (
                    id,
                    name
                )
            `)
            .eq('competition_id', competitionId);
        if (error) throw error;
        
        // Trasforma il risultato per compatibilità
        const teams = data.map(item => ({
            id: item.teams.id,
            name: item.teams.name
        }));
        
        console.log('Squadre del campionato caricate:', teams); // Debug
        return teams;
    }

    static async deleteTeam(id) {
        // Prima elimina tutti i collegamenti della squadra
        await window.supabaseClient
            .from('team_competitions')
            .delete()
            .eq('team_id', id);
            
        // Poi elimina la squadra
        const { error } = await window.supabaseClient
            .from('teams')
            .delete()
            .eq('id', id);
        if (error) throw error;
        console.log('Squadra eliminata:', id); // Debug
    }

    static async removeTeamFromCompetition(teamId, competitionId) {
        const { error } = await window.supabaseClient
            .from('team_competitions')
            .delete()
            .eq('team_id', teamId)
            .eq('competition_id', competitionId);
        if (error) throw error;
        console.log('Team rimosso dal campionato:', { teamId, competitionId }); // Debug
    }

    static async getCompetitionsByTeam(teamId) {
        const { data, error } = await window.supabaseClient
            .from('team_competitions')
            .select(`
                competition_id,
                competitions (
                    id,
                    name,
                    type,
                    season
                )
            `)
            .eq('team_id', teamId);
        if (error) throw error;
        
        // Trasforma il risultato per compatibilità
        const competitions = data.map(item => ({
            id: item.competitions.id,
            name: item.competitions.name,
            type: item.competitions.type,
            season: item.competitions.season
        }));
        
        console.log('Campionati della squadra caricati:', competitions); // Debug
        return competitions;
    }

    static async isTeamInCompetition(teamId, competitionId) {
        const { data, error } = await window.supabaseClient
            .from('team_competitions')
            .select('*')
            .eq('team_id', teamId)
            .eq('competition_id', competitionId)
            .single();
        
        if (error && error.code !== 'PGRST116') throw error; // PGRST116 = no rows found
        return !!data;
    }
}

// Gestione Campionati
window.CompetitionManager = class CompetitionManager {
    static async testConnection() {
        console.log('Testando connessione al database...'); // Debug
        try {
            const { data, error } = await window.supabaseClient
                .from('competitions')
                .select('count(*)')
                .limit(1);
            
            console.log('Test connessione - data:', data, 'error:', error); // Debug
            return { success: true, data, error };
        } catch (err) {
            console.error('Errore test connessione:', err); // Debug
            return { success: false, error: err };
        }
    }
    
    static async createCompetition(name, type, season) {
        console.log('CompetitionManager.createCompetition chiamato con:', { name, type, season }); // Debug
        console.log('Supabase client disponibile:', !!window.supabaseClient); // Debug
        
        // Prima testiamo la connessione
        const testResult = await this.testConnection();
        console.log('Risultato test connessione:', testResult); // Debug
        
        try {
            const { data, error } = await window.supabaseClient
                .from('competitions')
                .insert([{ name, type, season }])
                .select()
                .single();
            
            console.log('Risposta Supabase - data:', data, 'error:', error); // Debug
            
            if (error) {
                console.error('Errore Supabase:', error); // Debug
                throw error;
            }
            
            console.log('Campionato creato con successo:', data); // Debug
            return data;
        } catch (err) {
            console.error('Errore in createCompetition:', err); // Debug
            throw err;
        }
    }

    static async getAllCompetitions() {
        const { data, error } = await window.supabaseClient
            .from('competitions')
            .select('*')
            .order('created_at', { ascending: false });
        if (error) throw error;
        console.log('Campionati caricati:', data); // Debug
        return data;
    }

    static async getActiveCompetition() {
        const { data, error } = await window.supabaseClient
            .from('competitions')
            .select('*')
            .eq('status', 'active')
            .single();
        if (error && error.code !== 'PGRST116') throw error; // PGRST116 = no rows returned
        console.log('Campionato attivo:', data); // Debug
        return data;
    }

    static async updateCompetition(competitionId, updates) {
        const { data, error } = await window.supabaseClient
            .from('competitions')
            .update(updates)
            .eq('id', competitionId)
            .select()
            .single();
        if (error) throw error;
        console.log('Campionato aggiornato:', data); // Debug
        return data;
    }

    static async deleteCompetition(id) {
        // Prima elimina tutti i collegamenti delle squadre a questo campionato
        await window.supabaseClient
            .from('team_competitions')
            .delete()
            .eq('competition_id', id);
            
        // Poi elimina il campionato
        const { error } = await window.supabaseClient
            .from('competitions')
            .delete()
            .eq('id', id);
        if (error) throw error;
        console.log('Campionato eliminato:', id); // Debug
    }
}

// Gestione Calendario
window.MatchManager = class MatchManager {
    static generateCalendar(teams) {
        const numTeams = teams.length;
        if (numTeams % 2 !== 0) {
            teams.push({ id: 'bye', name: 'Riposa' });
        }
        
        const rounds = [];
        const numRounds = teams.length - 1;
        const numMatchesPerRound = teams.length / 2;

        // Algoritmo di Berger per la generazione del calendario
        for (let round = 0; round < numRounds; round++) {
            const matches = [];
            for (let match = 0; match < numMatchesPerRound; match++) {
                const home = (round + match) % (teams.length - 1);
                const away = (teams.length - 1 - match + round) % (teams.length - 1);
                
                if (match === 0) {
                    matches.push({
                        home: teams[round % 2 === 0 ? teams.length - 1 : 0],
                        away: teams[round % 2 === 0 ? 0 : teams.length - 1]
                    });
                } else {
                    matches.push({
                        home: teams[home + 1],
                        away: teams[away + 1]
                    });
                }
            }
            rounds.push({ round: round + 1, matches });
        }

        // Genera il girone di ritorno
        const returnRounds = rounds.map((round, index) => ({
            round: rounds.length + index + 1,
            matches: round.matches.map(match => ({
                home: match.away,
                away: match.home
            }))
        }));

        return [...rounds, ...returnRounds];
    }

    static async saveCalendar(competitionId, calendar) {
        const matches = calendar.flatMap(round => 
            round.matches.map(match => ({
                competition_id: competitionId,
                home_team_id: match.home.id,
                away_team_id: match.away.id,
                round: round.round,
                is_return: round.round > calendar.length / 2
            }))
        );

        const { error } = await window.supabaseClient
            .from('matches')
            .insert(matches);
        if (error) throw error;
        console.log('Calendario creato per il campionato:', competitionId); // Debug
    }

    static async getMatches(competitionId) {
        const { data, error } = await window.supabaseClient
            .from('matches')
            .select(`
                *,
                home_team:teams!matches_home_team_id_fkey(name),
                away_team:teams!matches_away_team_id_fkey(name)
            `)
            .eq('competition_id', competitionId)
            .order('round');
        if (error) throw error;
        console.log('Partite caricate per il campionato:', competitionId); // Debug
        return data;
    }

    static async updateResult(matchId, homeScore, awayScore) {
        const { error } = await window.supabaseClient
            .from('matches')
            .update({ 
                home_score: homeScore, 
                away_score: awayScore,
                played: true 
            })
            .eq('id', matchId);
        if (error) throw error;
        console.log('Risultato aggiornato per la partita:', matchId); // Debug
    }
}

// Gestione Classifica
window.StandingsManager = class StandingsManager {
    static async getStandings(competitionId) {
        // Recupera tutte le partite giocate
        const { data: matches, error } = await window.supabaseClient
            .from('matches')
            .select(`
                *,
                home_team:teams!matches_home_team_id_fkey(name),
                away_team:teams!matches_away_team_id_fkey(name)
            `)
            .eq('competition_id', competitionId)
            .eq('played', true);

        if (error) throw error;
        console.log('Partite per classifica caricate:', matches); // Debug

        // Inizializza la classifica
        const standings = new Map();

        // Processa ogni partita
        matches.forEach(match => {
            const homeTeam = match.home_team.name;
            const awayTeam = match.away_team.name;

            // Inizializza le squadre se non presenti
            if (!standings.has(homeTeam)) {
                standings.set(homeTeam, {
                    team: homeTeam,
                    played: 0,
                    won: 0,
                    drawn: 0,
                    lost: 0,
                    goalsFor: 0,
                    goalsAgainst: 0,
                    goalDifference: 0,
                    points: 0,
                    matchesAway: 0,
                    matchesHome: 0,
                    pointsAway: 0,
                    pointsHome: 0
                });
            }
            if (!standings.has(awayTeam)) {
                standings.set(awayTeam, {
                    team: awayTeam,
                    played: 0,
                    won: 0,
                    drawn: 0,
                    lost: 0,
                    goalsFor: 0,
                    goalsAgainst: 0,
                    goalDifference: 0,
                    points: 0,
                    matchesAway: 0,
                    matchesHome: 0,
                    pointsAway: 0,
                    pointsHome: 0
                });
            }

            const homeStats = standings.get(homeTeam);
            const awayStats = standings.get(awayTeam);

            // Aggiorna le statistiche
            homeStats.played++;
            awayStats.played++;
            homeStats.matchesHome++;
            awayStats.matchesAway++;

            homeStats.goalsFor += match.home_score;
            homeStats.goalsAgainst += match.away_score;
            awayStats.goalsFor += match.away_score;
            awayStats.goalsAgainst += match.home_score;

            if (match.home_score > match.away_score) {
                homeStats.won++;
                homeStats.points += 3;
                homeStats.pointsHome += 3;
                awayStats.lost++;
            } else if (match.home_score < match.away_score) {
                awayStats.won++;
                awayStats.points += 3;
                awayStats.pointsAway += 3;
                homeStats.lost++;
            } else {
                homeStats.drawn++;
                awayStats.drawn++;
                homeStats.points += 1;
                awayStats.points += 1;
                homeStats.pointsHome += 1;
                awayStats.pointsAway += 1;
            }

            homeStats.goalDifference = homeStats.goalsFor - homeStats.goalsAgainst;
            awayStats.goalDifference = awayStats.goalsFor - awayStats.goalsAgainst;
        });

        // Converti la Map in array e ordina
        return Array.from(standings.values()).sort((a, b) => {
            if (b.points !== a.points) return b.points - a.points;
            if (b.goalDifference !== a.goalDifference) return b.goalDifference - a.goalDifference;
            if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
            return a.team.localeCompare(b.team);
        });
    }

    static calculateMediaInglese(stats) {
        // La media inglese è la differenza tra i punti fatti in trasferta 
        // e i punti persi in casa (dove una vittoria vale 3 punti)
        const maxHomePoints = stats.matchesHome * 3;
        const mediaInglese = stats.pointsAway - (maxHomePoints - stats.pointsHome);
        return mediaInglese;
    }
}

// Gestione Albo d'Oro
window.ChampionsManager = class ChampionsManager {
    static async addChampion(competitionId, teamId, season) {
        const { error } = await window.supabaseClient
            .from('champions')
            .insert([{ competition_id: competitionId, team_id: teamId, season }]);
        if (error) throw error;
        console.log('Campione aggiunto:', { competitionId, teamId, season }); // Debug
    }

    static async getChampions() {
        const { data, error } = await window.supabaseClient
            .from('champions')
            .select(`
                *,
                competition:competitions(name, type),
                team:teams(name)
            `)
            .order('season', { ascending: false });
        if (error) throw error;
        console.log('Albo d\'oro caricato:', data); // Debug
        return data;
    }
}

console.log('Championship.js caricato completamente'); // Debug
