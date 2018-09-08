import csv


leagues_kept = {
    ('France', 'Ligue 1'),
    ('France', 'Ligue 1 '),
    ('Germany', 'Bundesliga'),
    ('Germany', 'Bundesliga '),
    ('Germany', '2. Bundesliga '),
    ('Germany', '2. Bundesliga'),
    ('Portugal', 'Primeira Liga '),
    ('England', 'Premier League '),
    ('England', 'Premier League'),
    ('Spain', 'Primera Division '),
    ('Italy', 'Serie A '),
    ('Italy', 'Serie A'),
}

file = 'historique_paris_sportifs.csv'
countries = set()
leagues = set()
teams = set()
seasons = set()
filtered = []
with open(file, 'r', newline='') as csvfile:
    def transcript_teams(team):
        a = {
                'AC Ajaccio': 'Ajaccio',
                'GFC Ajaccio': 'Ajaccio GFCO'
        }
        if team in a:
            return a[team]
        return team


    reader = csv.DictReader(csvfile, delimiter=';')
    i = 0
    for r in reader:

        if (r['Country'], r['League'])  not in leagues_kept:
            continue

        i += 1
        d = r['Date']
        row = {
            'Date': "{}/{}/{}".format(d[:2], d[3:5], d[-2:]),
            'Season': r['Season'][:4],
            'Country': r['Country'].strip(),
            'League': r['League'].strip(),
            'HomeTeam': transcript_teams(r['HomeTeam']),
            'AwayTeam': transcript_teams(r['AwayTeam']),
            'FTHG': r['FTHG'],
            'FTAG': r['FTAG'],
            'FDR': r['FDR'],
        }
        r['B365_2'] = r['P365_2']
        for sites in ['PI', 'B365']:
            for match in ['_1', '_N', '_2']:
                try:
                    row[sites + match] = float(r[sites + match].replace(',', '.'))
                except:
                    row[sites + match] = ''
                    #print(r['Country'])
        #print(r['League'])
        countries.add(r['Country'])
        leagues.add((r['Country'], r['League']))
        teams.add(r['HomeTeam'])
        teams.add(r['AwayTeam'])
        seasons.add(row['Season'])
        filtered.append(row)
print(countries)
print(leagues)
print(teams)
print(seasons)
fields = filtered[0].keys()
file = 'paris_sportifs_filtered.csv'
with open(file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, delimiter=',', fieldnames=fields)
    writer.writeheader()
    for row in filtered:
        writer.writerow(row)


