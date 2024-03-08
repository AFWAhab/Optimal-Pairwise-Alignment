import numpy as np
from Bio import SeqIO


class Costs:
    def __init__(self, gap_cost):
        self.matrix = np.matrix('10 2 5 2; 2 10 2 5; 5 2 10 2; 2 5 2 10')
        self.gap_cost = gap_cost
        self.base_to_index = {'A': 0, 'C': 1, 'G': 2, 'T': 3}


def find_cost(base_1: str, base_2: str, cost: Costs):
    res = cost.matrix[cost.base_to_index[base_1], cost.base_to_index[base_2]]
    return res


def optimal_alignment(seq_1: str, seq_2: str, cost: Costs, table=None, i=None, j=None):
    if table is None:
        table = np.full((len(seq_1) + 1, len(seq_2) + 1), np.nan)
    table[0][0] = 0
    if i is None:
        i = len(seq_1)
    if j is None:
        j = len(seq_2)

    if np.isnan(table[i, j]):
        v1 = v2 = v3 = v4 = np.nan
        if (i > 0) and (j > 0):
            v1 = optimal_alignment(seq_1, seq_2, cost, table=table, i=i - 1, j=j - 1)[1] + find_cost(seq_1[i - 1],
                                                                                                     seq_2[j - 1], cost)
        else:
            v1 = float('-inf')
        if i > 0:
            v2 = optimal_alignment(seq_1, seq_2, cost, table=table, i=i - 1, j=j)[1] + costs.gap_cost
        else:
            v2 = float('-inf')
        if j > 0:
            v3 = optimal_alignment(seq_1, seq_2, cost, table=table, i=i, j=j - 1)[1] + costs.gap_cost
        else:
            v3 = float('-inf')
        if i == 0 and j == 0:
            v4 = 0
        else:
            v4 = float('-inf')
        table[i][j] = max(v1, v2, v3, v4)
    return table, table[i][j]


def read_fasta(fasta_file):
    seq_record_list = []
    for seq_record in SeqIO.parse(fasta_file, "fasta"):
        seq_record_list.append(seq_record.seq)
    return seq_record_list


def backtrack(table, seq_1, seq_2, cost: Costs, i=None, j=None, acc = []):
    if i is None and j is None:
        i = len(seq_1)
        j = len(seq_2)
    if i == 0 and j == 0:
        return [("", "")]

    alignments = []

    if (i > 0) and (j > 0) and table[i][j] == table[i - 1][j - 1] + find_cost(seq_1[i - 1], seq_2[j - 1], cost):
        results = backtrack(table, seq_1, seq_2, cost, i - 1, j - 1)
        for res1, res2 in results:
            alignments.append((res1 + seq_1[i-1], res2 + seq_2[j-1]))

    if (i > 0) and (j >= 0) and table[i][j] == table[i - 1][j] + cost.gap_cost:
        results  = backtrack(table, seq_1, seq_2, cost, i - 1, j)
        for res1, res2 in results:
            alignments.append((res1 + seq_1[i - 1], res2 + "-"))

    if (i >= 0) and (j > 0) and table[i][j] == table[i][j - 1] + cost.gap_cost:
        results = backtrack(table, seq_1, seq_2, cost, i, j - 1)
        for res1, res2 in results:
            alignments.append((res1 + '-', res2 + seq_2[j - 1]))
    return alignments

if __name__ == '__main__':
    seq_1 = 'AATAAT'
    seq_2 = 'AAGG'
    seq_1_fasta = read_fasta('fastaFiles/seq1.fasta')
    seq_2_fasta = read_fasta('fastaFiles/seq2.fasta')
    costs = Costs(5)
    optimal_score = optimal_alignment(seq_1, seq_2, costs)
    optimal_table, optimal_value = optimal_score = optimal_alignment(seq_2, seq_1, costs)
    print(optimal_value)
    alignments = backtrack(optimal_table, seq_2, seq_1, costs)
    for index, alignment in enumerate(alignments, start = 1):
        print(f"Optimal Alignment {index}:")
        print(alignment[0])
        print(alignment[1])