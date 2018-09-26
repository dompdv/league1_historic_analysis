import random
import statistics
import numpy as np
from itertools import product
import proba_table
import json

class ModelAttackDefense:
    def __init__(self, n_teams, n_levels=4, max_goals=7, options=None):
        self.n_teams = n_teams
        # Number of levels of proficiency. A team has a probability vector of belonging to a certain level (a "bucket")
        self.n_levels = n_levels
        self.buckets = np.arange(0, n_levels)
        self.buckets_total = n_levels
        self.max_goals = max_goals  # Maximum possible goals per team during a match
        self.scores = np.arange(0, max_goals + 1)
        self.options = options
        if options and 'proba_table_file' in options:
            self.proba_table2 = proba_table.proba_table2(n_levels, file=options['proba_table_file'])
        elif options and 'matrices' in options:
            self.proba_table2 = proba_table.proba_table2(n_levels, matrices=options['matrices'])
        # Each team has a "attack_vector" and a "defense_vector"
        # representing the probability to belong to a level bucket
        if options and 'attack_vector' in options:
            self.attack_vector = options['attack_vector']
        else:
            self.attack_vector = [1 / self.buckets_total * np.ones((self.buckets_total,)) for _ in range(n_teams)]
        if options and 'defense_vector' in options:
            self.defense_vector = options['defense_vector']
        else:
            self.defense_vector = [1 / self.buckets_total * np.ones((self.buckets_total,)) for _ in range(n_teams)]
        # Statistics
        self.attack_average = []
        self.defense_average = []
        self.attack_mean = 0
        self.defense_mean = 0
        self.dirty_statistics = True
        self.update_stats()
        # Pretty printing team names
        self.teams = None
        if options and 'teams' in options:
            self.teams = options['teams']
            self.teams_max_length = max(len(s) for s in self.teams.values())

    def update_stats(self):
        if not self.dirty_statistics:
            return
        self.dirty_statistics = False
        self.attack_average = [np.sum(self.buckets * self.attack_vector[team]) for team in range(self.n_teams)]
        self.attack_mean = statistics.mean(self.attack_average)
        self.defense_average = [np.sum(self.buckets * self.defense_vector[team]) for team in range(self.n_teams)]
        self.defense_mean = statistics.mean(self.defense_average)

    def account_for2(self, team_1, team_2, score_1, score_2):
        L = self.n_levels
        p_team_1_a = self.attack_vector[team_1]
        p_team_1_d = self.defense_vector[team_1]
        p_team_2_a = self.attack_vector[team_2]
        p_team_2_d = self.defense_vector[team_2]

        # Bayes !!
        p_team_1_a.shape = (L, 1, 1, 1)
        p_team_1_d.shape = (1, L, 1, 1)
        p_team_2_a.shape = (1, 1, L, 1)
        p_team_2_d.shape = (1, 1, 1, L)
        # transform in to GD/TG reference
        gd = score_1 - score_2
        gd = max(-1, min(gd, 1)) + 1
        tg = (score_1 + score_2) // 3
        tg = min(2, tg)
        probabilities = self.proba_table2[:, :, :, :, tg, gd] * p_team_1_a * p_team_1_d * p_team_2_a * p_team_2_d
        # re-normalize
        s = np.sum(probabilities)
        probabilities = probabilities / s
        # accumulate attack_vector per user
        # No absolute 0 to avoid "black hole" effect
        self.attack_vector[team_1] = np.sum(probabilities, axis=(1,2,3))  + 0.001
        self.defense_vector[team_1] = np.sum(probabilities, axis=(0,2,3)) + 0.001
        self.attack_vector[team_2] = np.sum(probabilities, axis=(0,1,3)) + 0.001
        self.defense_vector[team_2] = np.sum(probabilities, axis=(0,1,2)) + 0.001
        # renormalisation à cause de la bidouille + 0.01
        self.attack_vector[team_1]= self.attack_vector[team_1] / sum(self.attack_vector[team_1])
        self.defense_vector[team_1]= self.defense_vector[team_1] / sum(self.defense_vector[team_1])
        self.attack_vector[team_2]= self.attack_vector[team_2] / sum(self.attack_vector[team_2])
        self.defense_vector[team_2]= self.defense_vector[team_2] / sum(self.defense_vector[team_2])
        # Statistics are dirty
        self.dirty_statistics = True

    def compute_outcome_probabilities(self, team_1, team_2, printing=False):
        L = self.n_levels
        p_team_1_a = self.attack_vector[team_1]
        p_team_1_d = self.defense_vector[team_1]
        p_team_2_a = self.attack_vector[team_2]
        p_team_2_d = self.defense_vector[team_2]
        # Bayes !!
        p_team_1_a.shape = (L, 1, 1, 1)
        p_team_1_d.shape = (1, L, 1, 1)
        p_team_2_a.shape = (1, 1, L, 1)
        p_team_2_d.shape = (1, 1, 1, L)
        scores = {}
        p = p_team_1_a * p_team_1_d * p_team_2_a * p_team_2_d
        for gd, tg in product(range(3), range(3)):
            probabilities = self.proba_table2[:, :, :, :, tg, gd] * p
            t = np.sum(probabilities)
            scores[(tg, gd)] = t
        breakdown = [(p, 0, 0) if gd == 2 else ((0, p, 0) if gd == 1 else (0, 0, p)) for (_, gd), p in scores.items()]
        p_1, p_n, p_2 = 0, 0, 0
        for a,b,c in breakdown:
            p_1 += a
            p_n += b
            p_2 += c
        return scores, (p_1, p_n, p_2)

    def print(self, limited=False):
        self.update_stats()
        if self.teams:
            print("Team" + (" " * (self.teams_max_length - 3))+ "|", end="")
        print("  #  |", end="")
        print("{0:^3}|".format(''), end="")
        for bucket in range(0, self.n_levels):
            print("{0:^5} | ".format(bucket), end='')
        print("{0:^6}|".format('Total'), end="")
        print("{0:^5}|".format('Avg A'), end="")
        print("{0:^4}|".format(''), end="")
        for bucket in range(0, self.n_levels):
            print("{0:^5} | ".format(bucket), end='')
        print("{0:^5}|".format('Total'), end="")
        print("{0:^6}|".format('Avg D'), end="")
        print()
        for team in range(self.n_teams):
            if limited and team not in limited:
                continue
            team_name = self.teams[team] if self.teams else str(team)

            if self.teams:
                f = "{0:^" + str(self.teams_max_length + 1) + "}|"
                print(f.format(team_name), end="")
            total = 0
            average = 0
            print("{0:^5}|".format(team), end="")
            print("{0:^3}|".format('A'), end="")
            for bucket in range(0, self.n_levels):
                print("{0:^5.0f} | ".format(100 * self.attack_vector[team][bucket]), end='')
                total += 100 * self.attack_vector[team][bucket]
                average += self.attack_vector[team][bucket] * bucket
            print("{0:^4.0f} | ".format(total), end='')
            print("{0:^4.1f} | ".format(average), end='')
            total = 0
            average = 0
            print("{0:^3}|".format('D'), end="")
            for bucket in range(0, self.n_levels):
                print("{0:^5.0f} | ".format(100 * self.defense_vector[team][bucket]), end='')
                total += 100 * self.defense_vector[team][bucket]
                average += self.defense_vector[team][bucket] * bucket
            print("{0:^4.0f} | ".format(total), end='')
            print("{0:^4.1f} | ".format(average), end='')
            print()


def draw_ps(ps):
    return random.choices(list(ps.keys()), weights=list(ps.values()))[0]

'''
    r = random.random()
    s, t = 0, 0
    for s, p in ps.items():
        t += p
        if t > r:
            return s
    return s
'''


def print_p(proba, threshold=0.02):
    print("Probabilities by score")
    [print("{:^5d}|".format(i), end='') for i, p in proba.items() if p > threshold]
    print()
    [print("{:^5.0f}|".format(p * 100), end='') for i, p in proba.items() if p > threshold]
    print()
