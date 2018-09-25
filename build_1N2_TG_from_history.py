import csv
import itertools

def write_matrices_to_file(rebuilt_matrices, to_file):
    if to_file is not '':
        with open(to_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=',', fieldnames=['Aa', 'Ad', 'Ba', 'Bd', 'l', 'tg', 'gd', 'p'])
            writer.writeheader()
            for (Aa, Ad, Ba, Bd), r in rebuilt_matrices.items():
                if 'p' not in r:
                    continue
                p = r['p']
                l = r['l']
                for tg, row in enumerate(p):
                    for gd, probability in enumerate(row):
                        w_r = {'Aa': Aa, 'Ad':Ad, 'Ba':Ba, 'Bd':Bd, 'l':l, 'tg':tg, 'gd':gd, 'p':probability}
                        writer.writerow(w_r)

def write_matrices_flat_to_file(rebuilt_matrices, to_file):
    if to_file is not '':
        with open(to_file, 'w', newline='') as csvfile:
            first = False
            fieldnames = ['Aa', 'Ad', 'Ba', 'Bd', 'l']
            for (Aa, Ad, Ba, Bd), r in rebuilt_matrices.items():
                if 'p' not in r:
                    continue
                p = r['p']
                l = r['l']
                if not first:
                    for tg, row in enumerate(p):
                        for gd, _ in enumerate(row):
                            fieldnames.append("({},{})".format(tg, gd))
                    writer = csv.DictWriter(csvfile, delimiter=',',fieldnames=fieldnames)
                    writer.writeheader()
                    first = True
                w_r = {'Aa': Aa, 'Ad': Ad, 'Ba': Ba, 'Bd': Bd, 'l': l}
                for tg, row in enumerate(p):
                    for gd, probability in enumerate(row):
                        w_r["({},{})".format(tg, gd)] = probability
                writer.writerow(w_r)


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
def build_missing_data(stats, threshold_1, threshold_2, filter_threshold):
    stats_rebuilt = {}
    for k, r in list(stats.items()):
        if r['l'] >= threshold_1:
            stats_rebuilt[k]  = r
            continue
        # ordonne les vecteurs proches par distance croissante
        closest = sorted([(kc, rc['l'], dist_v(k, kc)) for kc, rc in stats.items() if rc['l'] > filter_threshold], key=lambda x:x[2])
        closest_l = list(itertools.takewhile(lambda x: x < threshold_2, itertools.accumulate(l for _, l, _ in closest)))
        closest = closest[:len(closest_l) + 1]
        new_matrix = [[0 for _ in row] for row in r['s']]
        t = 0
        for kc, l, d in closest:
            f = l / (1+d)
            t += f
            new_matrix = [
                [x1 + f * y1 for x1, y1 in zip(x,y)] for x,y in zip(new_matrix, stats[kc]['p'])
            ]
        #t = sum(l for _, l ,_ in closest)
        if t > 0:
            new_matrix = [ [x1 / t for x1 in x] for x in new_matrix]
        stats_rebuilt[k] =  {
            'p': new_matrix,
            'l': sum(l for _, l ,_ in closest)
        }
    return stats_rebuilt


def compute_1N2_TG_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat):
    # Regroupement des scores par classes d'attaque
    base_statistics = {}  # dictionnaire indexé par (Aa, Ad, Ba, Bd, s1, s2)
    s_stats = {}   # dictionnaire indexé par (Aa, Ad, Ba, Bd} = { 's': {(s1,s2):nbre de buts, 'p':(s1,s2):proba, 'l':# échantillons)

    # initialise base_2
    ra = range(n_cat)
    #sca = range(min_score, max_score + 1)
    sca = range(3)  # 0-1, 1-2, 3-4, 5+  (divise par 3)
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


# =================================================================================================
## Load data from files, identify teams and number of matches per team
def load_compute_matrices(from_year, to_year, threshold_1, threshold_2, filter_threshold, n_cat, from_file):
    matches, total_match, teams, teams_count, min_score, max_score = load_data(from_file, from_year, to_year)

    ## Séparer les équipes en groupes de meilleurs attaquants et défenseur
    attack_group, defense_group = split_teams_by_seasons_into_groups(matches, teams, n_cat)

    # Première approche : cumuler par Aa,Ad, Ba,Bd,s1,s2
    s_stats = compute_1N2_TG_statistics(matches, attack_group, defense_group, min_score, max_score, n_cat)

    filtered = {k:v for k, v in s_stats.items() if v['l'] > filter_threshold}

    rebuilt = build_missing_data(s_stats, threshold_1, threshold_2, filter_threshold)

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
    write_matrices_to_file(stats, 'matrices_cat{}.csv'.format(n_cat))
    write_matrices_flat_to_file(stats, 'matrices_flat_cat{}.csv'.format(n_cat))
    write_matrices_flat_to_file(rebuilt, 'matrices_flat_rebuilt_cat{}.csv'.format(n_cat))
    write_matrices_flat_to_file(filtered, 'matrices_flat_filtered_cat{}.csv'.format(n_cat))
