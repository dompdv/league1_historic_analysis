from build_matrices_from_history import load_compute_matrices
import numpy as np
from sklearn.decomposition import PCA, IncrementalPCA


def build_np_matrix(matrices):
    def find_sizes(matrices):
        l = 0
        for v in matrices.values():
            if 'p' in v:
                l += 1
        for v in matrices.values():
            if 'p' in v:
                return l, len(v['p']), len(v['p'][0])

    n_matrices, rows, columns = find_sizes(matrices)
    vectors = np.zeros((n_matrices, rows * columns))
    index = 0
    for k, v in matrices.items():
        if 'p' not in v:
            continue
        for r in range(rows):
            for c in range(columns):
                vectors[index, r * columns + c] = v['p'][c][r]
        matrices[k]['index'] = index
        index += 1
    return n_matrices, rows, columns, vectors, matrices

n_cat = 4
matrices, rebuilt, filtered = load_compute_matrices(
    1900, 2020,
    threshold_1=1,
    threshold_2=1,
    filter_threshold=40,
    n_cat=n_cat,
    from_file='paris_sportifs_filtered.csv'
)

n_matrices, rows, columns, vectors, indexed_matrices = build_np_matrix(filtered)
#log_vectors = np.log(vectors)
n_comp = 3
mean_vectors = np.mean(vectors, axis=0)
pca = PCA(n_components=n_comp)
pca = IncrementalPCA(n_components=n_comp)
to_fit = vectors - mean_vectors
transformed = pca.fit_transform(to_fit)
print(pca.explained_variance_ratio_)
print(pca.explained_variance_)

max_list = []
for index in range(len(vectors)):
    base = mean_vectors.copy()
    for i, alpha in enumerate(transformed[index]):
        base += alpha * pca.components_[i]
    max_list.append(np.max(np.abs(vectors[index] - base)))

print(max_list)
print(max(max_list))
#X = pca.transform(X)


