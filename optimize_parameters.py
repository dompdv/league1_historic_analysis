from build_1N2_TG_from_history import load_compute_matrices
from backtesting import simulate_bet_over
from collections import OrderedDict
from itertools import product

database = []

from_year = 2015
to_year = 2018

full_data = {}

dataset = product(range(1900,1901), range(2015, 2016), range(2,4,1), range(1,202,50), range(1,202,50))

#optimal
dataset = product(range(1900,1901), range(2016, 2017), range(3,4,1), range(1,201,50), range(1,201,50))

dataset = product(range(1900,1901), range(2015, 2016), range(3,5,1), range(1,102,50), range(1,102,50))
for data_from_year, data_to_year, n_cat, t1, t2 in dataset:
    stats, rebuilt, filtered = load_compute_matrices(
        data_from_year,
        data_to_year,
        threshold_1=t1,
        threshold_2=t2,
        filter_threshold=t1,
        n_cat=n_cat,
        from_file='paris_sportifs_filtered.csv'
    )
    play_scores, bet_details, final_model = simulate_bet_over(data_from_year, data_to_year, from_year, to_year,
                                                              proba_table_file='', n_cat=n_cat, matrices=rebuilt,
                                                              printing=False)
    for season, r in play_scores.items():
        print("Season {:^5} Total {:^5.0f} {:^5.3f} Prono {:^5.0f} {:^5.3f} Exact {:^5.0f} {:^5.3f} Gain {:^5.0f} Stake:{:^5.0f} ROI:{:^5.0f}".format(
            season, r['total'][0], r['total'][1], r['prono'][0], r['prono'][1], r['exact'][0], r['exact'][1],
            r['paris'][0], r['paris'][1], r['paris'][2] * 100
        ))
    for season, results in play_scores.items():
        row = OrderedDict()
        row['NCAT'] = n_cat
        row['Data_from'] = data_from_year
        row['Data_to'] = data_to_year
        row['Season'] = season
        row['T1'] = str(t1)
        row['T2'] = str(t2)
        row['total'] = str(results['total'][0])
        row['prono'] = str(results['prono'][0])
        row['exact'] = str(results['exact'][0])
        row['paris_gain'] = str(int(results['paris'][0]))
        row['paris_stake'] = str(int(results['paris'][1]))
        row['paris_roi'] = "{:.2f}".format(100 * results['paris'][2])
        database.append(row)


first_row = False
for row in database:
    if not first_row:
        first_row = True
        print(",".join(row.keys()))
    print(','.join([str(r) for r in row.values()]))
