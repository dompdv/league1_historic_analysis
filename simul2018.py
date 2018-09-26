import teams_data
from modelattackdefense import ModelAttackDefense
import data_matches_2018
import numpy as np
import simul2018_data
from build_1N2_TG_from_history import load_compute_matrices
from backtesting import simulate_bet_over

def teams_data_referential():
    # Build teams matches referential
    teams = teams_data.teams_data()
    teams_invert = {r['N']: k for k, r in teams.items()}
    return teams, teams_invert

# Load teams matches
teams, teams_invert = teams_data_referential()
teams_of_the_season = {teams[t]['N'] for t in teams if 2018 in teams[t]['seasons']}

data_from_year, data_to_year = 1900, 2019
t1, t2 = 50, 50
n_cat = 3
from_year = 2015
to_year = 2018
stats, rebuilt, filtered = load_compute_matrices(
    data_from_year,
    data_to_year,
    threshold_1=t1,
    threshold_2=t2,
    filter_threshold=t1,
    n_cat=n_cat,
    from_file='paris_sportifs_filtered.csv'
)
play_scores, bet_details, model = simulate_bet_over(data_from_year, data_to_year, from_year, to_year,
                                                          proba_table_file='', n_cat=n_cat, matrices=rebuilt,
                                                          printing=False)

#attack_vector, defense_vector = simul2018_data.attack_defense_vectors()

'''
Div = League Division
Date = Match Date (dd/mm/yy)
HomeTeam = Home Team
AwayTeam = Away Team
FTHG and HG = Full Time Home Team Goals
FTAG and AG = Full Time Away Team Goals
FTR and Res = Full Time Result (H=Home Win, D=Draw, A=Away Win)
'''
# Matches de la saison 2018
matches = data_matches_2018.calendar()
'''
# Initialisation du modèle
model = ModelAttackDefense(n_teams=len(teams),
                           options={
                               'teams': teams_invert,
                               'attack_vector': np.array(attack_vector),
                               'defense_vector': np.array(defense_vector),
                               'proba_table_file': 'data_built_m_20180813.csv'})
'''
model.print(teams_of_the_season)

matches = simul2018_data.account_for_2018_results(matches)
# Passer en revue les matchs passés et ajuster les probas
print("Ajustement sur les résultats des matchs passés")
last_day = 0
counter = 0
play_score = 0
play_score_prono = 0
play_score_exact = 0
for match in matches:
    if match['Played']:
        home_team_number, away_team_number = teams[match['HomeTeam']]['N'], teams[match['AwayTeam']]['N']
        s1, s2 = match['FTHG'], match['FTAG']
        print("Jour {} : {} / {} -> {}/{}".format(match['Date'], match['HomeTeam'], match['AwayTeam'], s1, s2))
        model.print(set([home_team_number, away_team_number]))
        model.account_for2(home_team_number, away_team_number, s1, s2)
        model.print(set([home_team_number, away_team_number]))
        last_day = match['Date']
        counter += 1
        if (s1 > s2 and match['Prono'] == 1) or (s1 == s2 and match['Prono'] == 0) or (s1 < s2 and match['Prono'] == 2):
            play_score += 3
            play_score_prono += 3
            if s1 == match['Exact_s1'] and s2 == match['Exact_s2']:
                play_score += 2
                play_score_exact += 2

model.print(teams_of_the_season)
print('Dernier jour joué:', last_day)
if counter > 0:
    print("Matchs joués: {}".format(counter))
    print("Score total / moyen = {} / {:3.2f}".format(play_score, play_score / counter))
    print("Score prono / moyen = {} / {:3.2f}".format(play_score_prono, play_score_prono / counter))
    print("Score exact / moyen = {} / {:3.2f}".format(play_score_exact, play_score_exact / counter))

# sur les matches futurs, mettre les pronostics (probas et scores,...)
print("Prochains matchs")
for match in matches:
    # Afficher les prochains matchs
    if not match['Played'] and match['Date'] <= last_day + 1:
        print("Jour {} {} ({}) contre {} ({})".format(match['Date'],
                                                      match['HomeTeam'],
                                                      teams[match['HomeTeam']]['Code'],
                                                      match['AwayTeam'],
                                                      teams[match['AwayTeam']]['Code'],
                                                      ))
        home_team_number, away_team_number = teams[match['HomeTeam']]['N'], teams[match['AwayTeam']]['N']
        scores, p_1_n_2 = model.compute_outcome_probabilities(home_team_number, away_team_number, printing=True)
        p_1, p_n, p_2 = p_1_n_2
        def choose_score(bet_on, p_1_n_2, scores):
            base = [
                [11.7, 7.2, 3.9, 1.2, 0.5, 0.1],
                [13.3, 13.8, 5.5, 2.0, 0.5, 0.0],
                [9.9, 8.6, 4.6, 1.1, 0.3, 0.1],
                [3.5, 4.5, 1.9, 0.4, 0.1, 0.0],
                [1.7, 1.3, 0.6, 0.2, 0.2, 0.0],
                [0.5, 0.3, 0.1, 0.1, 0.0, 0.0]
            ]
            index = [1, 2, 0][bet_on]
            possible_scores = []
            for (tg, gd), ptg in scores.items():
                if gd != index:
                    continue
                for s1, r in enumerate(base):
                    for s2, p in enumerate(r):
                        if (bet_on == 1 and s1 > s2) or (bet_on == 0 and s1 == s2) or (bet_on == 2 and s1 < s2):
                            if min((s1 + s2) // 3, 2) == tg:
                                possible_scores.append((s1, s2, p * ptg))
            possible_scores = sorted(possible_scores, key=lambda x: x[2], reverse=True)
            s1, s2, _ = possible_scores[0]
            return s1, s2

        print("1/N/2 = {:^5.2f},{:^5.2f},{:^5.2f}".format(p_1 * 100, p_n * 100, p_2 * 100))
        p_m = max(p_1_n_2)
        bet_on = 1 if p_m == p_1 else (2 if p_m == p_2 else 0)
        bet_s1, bet_s2 = choose_score(bet_on, p_1_n_2, scores)
        print("Bet on : {}, Score: {}/{}".format(bet_on, bet_s1, bet_s2))

