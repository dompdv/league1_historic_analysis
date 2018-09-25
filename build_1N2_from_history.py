import csv
import itertools

# Load data from
def load_data(from_file, from_year, to_year):
    # Recupere les matches des dernières saisons
    matches = []
    with open(from_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for r in reader:
            season = int(r['Season'])
            if season not in range(from_year, to_year):
                continue
            row = {}
            for f in ['Date', 'HomeTeam', 'AwayTeam', 'Country', 'League']:
                row[f] = r[f].strip()
            skip = False
            for f in ['FTHG', 'FTAG', 'Season']:
                try:
                    row[f] = int(r[f])
                except:
                    skip = True
            if not skip:
                matches.append(row)

    # Trouve toutes les équipes
    teams = set(r['HomeTeam'] for r in matches) | set(r['AwayTeam'] for r in matches)
    # Liste complète des matches, chaque match apparaisant deux fois, une par équipe,
    # Determine le nombre de matches joués par équipe
    match_list = [r['HomeTeam'] for r in matches] + [r['AwayTeam'] for r in matches]
    teams_count = { t: match_list.count(t) for t in teams}
    total_match = len(match_list)
    # Plus petit et plus grand
    max_score = max(max(r['FTHG'], r['FTAG']) for r in matches)
    min_score = min(min(r['FTHG'], r['FTAG']) for r in matches)
    return matches, total_match, teams, teams_count, min_score, max_score

## Va chercher à séparer les équipes en groupes de meilleurs attaquants et défenseur
def split_teams_into_groups(matches, teams, n_cat):

    # On crée le meilleur groupe à la main. De niveau n_cat-1
    best_group = set(["Lyon", "Monaco", "Paris SG"])
    best_group = set()
    adjusted_teams = teams - best_group


    # Les matchs joués par équipe
    played = {t : [] for t in adjusted_teams}
    for r in matches:
        if r['HomeTeam'] in adjusted_teams:
            played[r['HomeTeam']].append(r)
        if r['AwayTeam'] in adjusted_teams:
            played[r['AwayTeam']].append(r)
    # Goals matked and received per team
    goal_marked = {t:0 for t in adjusted_teams}
    goal_received = {t:0 for t in adjusted_teams}
    for r in matches:
        if r['HomeTeam'] in adjusted_teams:
            goal_marked[r['HomeTeam']] += r['FTHG']
            goal_received[r['HomeTeam']] += r['FTAG']
        if r['AwayTeam'] in adjusted_teams:
            goal_marked[r['AwayTeam']] += r['FTAG']
            goal_received[r['AwayTeam']] += r['FTHG']
    # Average using the number of matches playes by a team
    # Nombre de buts moyens données ou recus. Les équipes sont classées par ordre de force croissante
    for t in adjusted_teams:
        goal_marked[t] /= len(played[t])
        goal_received[t] /= len(played[t])

    goal_marked_ordered = sorted(goal_marked.items(), key=lambda x:x[1], reverse=False)
    goal_received_ordered = sorted(goal_received.items(), key=lambda x:x[1], reverse=True)
    #print(goal_marked_ordered)
    #print(goal_received_ordered)

    # La répartition par groupe se fait de telle sorte que le nombre de matchs joués par groupe soit équivalent
    # sinon, à cause du bas de tableau changeant, on a une mauvaise répartition

    # OLD : grpoupes de même taille
    #group_size_old = len(goal_marked_ordered) / n_cat
    #attack_group_old = {t: int(i / group_size_old) for i,(t,_) in enumerate(goal_marked_ordered)}
    #defense_group_old = {t: int(i / group_size_old) for i,(t,_) in enumerate(goal_received_ordered)}

    total_match = sum(len(played[t]) for t in adjusted_teams)
    group_size = total_match / (n_cat - (1 if len(best_group) > 0 else 0))  # car j'ai séparé le groupe de tête à la main
    goal_marked_match = [len(played[t]) for t,_ in goal_marked_ordered]
    goal_marked_match = list(itertools.accumulate(goal_marked_match))
    goal_marked_match = [int(g / group_size) for g in goal_marked_match]
    attack_group = {t: min(g, n_cat - 1 - (1 if len(best_group) > 0 else 0)) for (t, _), g in zip(goal_marked_ordered, goal_marked_match)}
    #print(attack_group)

    goal_received_match = [len(played[t]) for t,_ in goal_received_ordered]
    goal_received_match = list(itertools.accumulate(goal_received_match))
    goal_received_match = [ int(g / group_size) for g in goal_received_match]
    defense_group = {t: min(g, n_cat - 1 - (1 if len(best_group) > 0 else 0)) for (t, _), g in zip(goal_received_ordered, goal_received_match)}
    #print(defense_group)

    # ajout du groupe de tête
    for t in best_group:
        defense_group[t] = n_cat - 1
        attack_group[t] = n_cat - 1
    return attack_group, defense_group

def compute_base_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat):
    # Regroupement des scores par classes d'attaque
    base_statistics = {}  # dictionnaire indexé par (Aa, Ad, Ba, Bd, s1, s2)
    base_2 = {}   # dictionnaire indexé par (Aa, Ad, Ba, Bd} = { 's': {(s1,s2):nbre de buts, 'p':(s1,s2):proba, 'l':# échantillons)

    # initialise base_2
    ra = range(n_cat)
    sca = range(min_score, max_score + 1)
    for Aa, Ad, Ba, Bd in itertools.product(ra, ra, ra, ra):
        base_2[(Aa, Ad, Ba, Bd)] = {'s': [[0 for _ in list(sca)] for _ in list(sca)], 'l': 0}

    for r in matches:
        Aa = attack_group[r['HomeTeam']]
        Ad = defense_group[r['HomeTeam']]
        Ba = attack_group[r['AwayTeam']]
        Bd = defense_group[r['AwayTeam']]
        s1 = r['FTHG']
        s2 = r['FTAG']
        k = (Aa, Ad, Ba, Bd, s1, s2)
        if k not in base_statistics:
            base_statistics[k] = 0
        base_statistics[k] += 1
        base_2[(Aa, Ad, Ba, Bd)]['l'] += 1
        base_2[(Aa, Ad, Ba, Bd)]['s'][s1][s2] += 1

    base_statistics = {k: v / len(matches) for k, v in base_statistics.items()}
    for Aa, Ad, Ba, Bd in itertools.product(ra, ra, ra, ra):
        n = base_2[(Aa, Ad, Ba, Bd)]['l']
        if n > 0:
            base_2[(Aa, Ad, Ba, Bd)]['p'] = [[base_2[(Aa, Ad, Ba, Bd)]['s'][i][j] / n for j in list(sca)] for i in list(sca)]

    return base_statistics, base_2

def write_matrices_to_file(rebuilt_matrices, to_file):
    if to_file is not '':
        with open(to_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=',', fieldnames=['Aa', 'Ad', 'Ba', 'Bd', 'l', 's1', 's2', 'p'])
            writer.writeheader()
            for (Aa, Ad, Ba, Bd), r in rebuilt_matrices.items():
                if 'p' not in r:
                    continue
                p = r['p']
                l = r['l']
                for s1, row in enumerate(p):
                    for s2, probability in enumerate(row):
                        w_r = {'Aa': Aa, 'Ad':Ad, 'Ba':Ba, 'Bd':Bd, 'l':l, 's1':s1, 's2':s2, 'p':probability}
                        writer.writerow(w_r)

def write_matrices_flat_to_file(rebuilt_matrices, to_file):
    if to_file is not '':
        with open(to_file, 'w', newline='') as csvfile:
            first = False
            fieldnames = ['Aa', 'Ad', 'Ba', 'Bd', 'l']
            for (Aa, Ad, Ba, Bd), r in rebuilt_matrices.items():
                if 'pgd' not in r or 'ptg' not in r:
                    continue
                pg = r['pgd']
                tg = r['ptg']
                l = r['l']
                if not first:
                    for k in pg:
                        fieldnames.append("GD_{}".format(k))
                    for k in tg:
                        fieldnames.append("TG_{}".format(k))
                    writer = csv.DictWriter(csvfile, delimiter=',',fieldnames=fieldnames)
                    writer.writeheader()
                    first = True
                w_r = {'Aa': Aa, 'Ad': Ad, 'Ba': Ba, 'Bd': Bd, 'l': l}
                for k, probability in pg.items():
                    w_r["GD_{}".format(k)] = probability
                for k, probability in tg.items():
                    w_r["TG_{}".format(k)] = probability
                writer.writerow(w_r)

def split_teams_by_seasons_into_groups(matches, teams, n_cat):

    # On crée le meilleur groupe à la main. De niveau n_cat-1
    # Les matchs joués par équipe
    played = {}
    for r in matches:
        season = r['Season']
        ht = "{}_{}".format(r['HomeTeam'], season)
        if ht not in played:
            played[ht] = [r]
        else:
            played[ht].append(r)
        at = "{}_{}".format(r['AwayTeam'], season)
        if at not in played:
            played[at] = [r]
        else:
            played[at].append(r)

    adjusted_teams = list(played.keys())
    # Goals matked and received per team
    goal_marked = {t:0 for t in adjusted_teams}
    goal_received = {t:0 for t in adjusted_teams}
    for r in matches:
        season = r['Season']
        ht = "{}_{}".format(r['HomeTeam'], season)
        at = "{}_{}".format(r['AwayTeam'], season)
        goal_marked[ht] += r['FTHG']
        goal_received[ht] += r['FTAG']
        goal_marked[at] += r['FTAG']
        goal_received[at] += r['FTHG']
    # Average using the number of matches playes by a team
    # Nombre de buts moyens données ou recus. Les équipes sont classées par ordre de force croissante
    for t in adjusted_teams:
        goal_marked[t] /= len(played[t])
        goal_received[t] /= len(played[t])

    goal_marked_ordered = sorted(goal_marked.items(), key=lambda x:x[1], reverse=False)
    goal_received_ordered = sorted(goal_received.items(), key=lambda x:x[1], reverse=True)
    #print(goal_marked_ordered)
    #print(goal_received_ordered)

    # groupes de même taille
    group_size = len(goal_marked_ordered) / n_cat
    attack_group = {t: int(i / group_size) for i,(t,_) in enumerate(goal_marked_ordered)}
    defense_group = {t: int(i / group_size) for i,(t,_) in enumerate(goal_received_ordered)}

    return attack_group, defense_group

# distance entre deux Aa, Ad, Ba, Bd
def dist_v(a, b):
    Aa, Ad, Ba, Bd = a
    Aa_, Ad_, Ba_, Bd_ = b
    return abs(Aa - Aa_) + abs(Ad - Ad_) + abs(Ba - Ba_) + abs(Bd - Bd_)

# Construit les stats manquantes
def build_matrices_rebuilt(stats, threshold_1, threshold_2, filter_threshold):
    stats_rebuilt = {}
    flat = [(k, r['pgd'],r['ptg'], r['l']) for k, r in stats.items() if r['l'] > 0]
    #data_full = sorted([(k, p, l) for k, p, l in flat if l > 0], key=lambda x: x[2], reverse=True)
    for k, r in list(stats.items()):
        if r['l'] >= threshold_1:
            stats_rebuilt[k]  = r
            continue
        # ordonne les vecteurs proches par distance croissante
        closest = sorted([(kc, rc['l'], dist_v(k, kc)) for kc, rc in stats.items() if rc['l'] > filter_threshold], key=lambda x:x[2])
        closest_l = list(itertools.takewhile(lambda x: x < threshold_2, itertools.accumulate(l for _, l, _ in closest)))
        closest = closest[:len(closest_l) + 1]
        new_matrix_pg = {k:0 for k,_ in r['gd'].items()}
        new_matrix_tg = {k:0 for k,_ in r['tg'].items()}
        t = 0
        for kc, l, d in closest:
            f = l / (1+d)
            t += f
            new_matrix_pg = {k:x + f * stats[kc]['pgd'][k] for k, x in new_matrix_pg.items()}
            new_matrix_tg = {k:x + f * stats[kc]['ptg'][k] for k, x in new_matrix_tg.items()}
        #t = sum(l for _, l ,_ in closest)
        new_matrix_pg = {k:x / t for k,x in new_matrix_pg.items()}
        new_matrix_tg = {k:x / t for k,x in new_matrix_tg.items()}
        stats_rebuilt[k] =  {
            'pgd': new_matrix_pg,
            'ptg': new_matrix_tg,
            'l': sum(l for _, l ,_ in closest)
        }
    return stats_rebuilt


def compute_1N2_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat):
    # Regroupement des scores par classes d'attaque
    base_statistics = {}  # dictionnaire indexé par (Aa, Ad, Ba, Bd, s1, s2)
    s_stats = {}   # dictionnaire indexé par (Aa, Ad, Ba, Bd} = { 's': {(s1,s2):nbre de buts, 'p':(s1,s2):proba, 'l':# échantillons)

    # initialise base_2
    ra = range(n_cat)
    #sca = range(min_score, max_score + 1)
    sca = range(3)  # 0-2, 3-5, 6+  (divise par 3)
    for Aa, Ad, Ba, Bd in itertools.product(ra, ra, ra, ra):
        s_stats[(Aa, Ad, Ba, Bd)] = {'s': [[0, 0, 0] for _ in list(sca)], 'l': 0}

    for r in matches:
        season = r['Season']
        ht = "{}_{}".format(r['HomeTeam'], season)
        at = "{}_{}".format(r['AwayTeam'], season)
        Aa = attack_group[ht]
        Ad = defense_group[ht]
        Ba = attack_group[at]
        Bd = defense_group[at]
        s1 = r['FTHG']
        s2 = r['FTAG']
        k = (Aa, Ad, Ba, Bd, s1, s2)
        if k not in base_statistics:
            base_statistics[k] = 0
        base_statistics[k] += 1
        gd = 1 if s1 > s2 else (-1 if s1 < s2 else 0)
        tg = min((s1 + s2) // 3, 2)
        s_stats[(Aa, Ad, Ba, Bd)]['l'] += 1
        s_stats[(Aa, Ad, Ba, Bd)]['s'][tg][gd + 1] += 1

    base_statistics = {k: v / len(matches) for k, v in base_statistics.items()}
    for Aa, Ad, Ba, Bd in itertools.product(ra, ra, ra, ra):
        n = s_stats[(Aa, Ad, Ba, Bd)]['l']
        if n > 0:
            s_stats[(Aa, Ad, Ba, Bd)]['p'] = [[s_stats[(Aa, Ad, Ba, Bd)]['s'][i][j] / n for j in range(3)] for i in list(sca)]

    return s_stats


def compute_simple_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat):
    # Regroupement des scores par classes d'attaque
    results = {}   # dictionnaire indexé par (Aa, Ad, Ba, Bd} = { 'gd': {(gd):nbre de buts de différecence, 'pgd':proba, 'l':# échantillons)

    # initialise base_2
    gd_range = range(-2, 3)
    tg_range = range(4)
    ra = range(n_cat)
    sca = range(min_score, max_score + 1)
    for Aa, Ad, Ba, Bd in itertools.product(ra, ra, ra, ra):
        results[(Aa, Ad, Ba, Bd)] = {
            'gd': {i:0 for i in list(gd_range)},
            'l': 0,
            'tg': {i: 0 for i in list(tg_range)}
        }

    for r in matches:
        season = r['Season']
        ht = "{}_{}".format(r['HomeTeam'], season)
        at = "{}_{}".format(r['AwayTeam'], season)
        Aa = attack_group[ht]
        Ad = defense_group[ht]
        Ba = attack_group[at]
        Bd = defense_group[at]
        s1 = r['FTHG']
        s2 = r['FTAG']
        results[(Aa, Ad, Ba, Bd)]['l'] += 1
        gd = s1 - s2
        gd = max(-2, gd)
        gd = min(2, gd)  # gd compris entre -2 et 2
        tg = min((s1 + s2) // 2, 3) # Nombre de couples de buts, 0-1, 2-3, 4-5, 6-7 ou plus
        results[(Aa, Ad, Ba, Bd)]['gd'][gd] += 1
        results[(Aa, Ad, Ba, Bd)]['tg'][tg] += 1

    for Aa, Ad, Ba, Bd in itertools.product(ra, ra, ra, ra):
        n = results[(Aa, Ad, Ba, Bd)]['l']
        if n > 0:
            results[(Aa, Ad, Ba, Bd)]['pgd'] = {i:results[(Aa, Ad, Ba, Bd)]['gd'][i] / n for i in list(gd_range)}
            results[(Aa, Ad, Ba, Bd)]['ptg'] = {i: results[(Aa, Ad, Ba, Bd)]['tg'][i] / n for i in list(tg_range)}
    return results


# =================================================================================================
## Load data from files, identify teams and number of matches per team
def load_compute_matrices(from_year, to_year, threshold_1, threshold_2, filter_threshold, n_cat, from_file):
    matches, total_match, teams, teams_count, min_score, max_score = load_data(from_file, from_year, to_year)

    ## Séparer les équipes en groupes de meilleurs attaquants et défenseur
    attack_group, defense_group = split_teams_by_seasons_into_groups(matches, teams, n_cat)

    # Première approche : cumuler par Aa,Ad, Ba,Bd,s1,s2
    #_, base_2 = compute_base_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat)
    #s_stats = compute_simple_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat)
    s_stats = compute_1N2_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat)

    filtered = {k:v for k, v in s_stats.items() if v['l'] > filter_threshold}

    rebuilt = build_matrices_rebuilt(s_stats, threshold_1, threshold_2, filter_threshold)

    return s_stats, rebuilt, filtered

if __name__ == "__main__":
    n_cat = 4
    stats, rebuilt, filtered = load_compute_matrices(
        1900, 2020,
        threshold_1=100,
        threshold_2=200,
        filter_threshold=100,
        n_cat=n_cat,
        from_file='paris_sportifs_filtered.csv'
    )
    write_matrices_flat_to_file(stats, 'matrices_flat_cat{}.csv'.format(n_cat))
    write_matrices_flat_to_file(rebuilt, 'matrices_flat_rebuilt_cat{}.csv'.format(n_cat))
    write_matrices_flat_to_file(filtered, 'matrices_flat_filtered_cat{}.csv'.format(n_cat))
