"""Stage 3 — clustering.

HDBSCAN over the stage-2 embeddings (brief section 4): no need to guess the
cluster count up front, and genuine outliers land in the noise bucket (-1),
which maps onto "no causal model yet" instead of being forced into a cluster.

Post-processing: clusters below ~10% of the batch are merged into their
nearest surviving neighbor so the dashboard shows a handful of meaningful
patterns instead of fragments.
"""

import math
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize

NOISE_CLUSTER_ID = -1


@dataclass
class ClusteringResult:
    labels: np.ndarray  # per-response cluster id; NOISE_CLUSTER_ID for outliers
    clusters: list[dict]  # schema per brief section 5: {cluster_id, student_ids, size}


def _centroids(reduced: np.ndarray, labels: np.ndarray, cluster_id: int) -> np.ndarray:
    members = reduced[labels == cluster_id]
    return members.mean(axis=0)


def merge_small_clusters(
    reduced: np.ndarray,
    labels: np.ndarray,
    min_fraction: float = 0.10,
) -> np.ndarray:
    """Fold clusters below min_fraction of the batch into nearest neighbor.

    Nearest = highest centroid cosine similarity in the same reduced space
    used for clustering. Noise (-1) is never merged into anything and is
    never a merge target. Returns a new label array; survivors keep ids of
    the cluster they joined.
    """
    labels = labels.copy()
    n = len(labels)
    threshold = min_fraction * n
    while True:
        cluster_ids = [c for c in sorted(set(labels.tolist())) if c != NOISE_CLUSTER_ID]
        undersized = [
            c for c in cluster_ids if (labels == c).sum() < threshold
        ]
        if not undersized or len(cluster_ids) < 2:
            break
        # Merge the smallest undersized cluster first.
        smallest = min(undersized, key=lambda c: int((labels == c).sum()))
        target_centroids = {
            c: _centroids(reduced, labels, c) for c in cluster_ids if c != smallest
        }
        src_centroid = _centroids(reduced, labels, smallest)
        best = max(
            target_centroids,
            key=lambda c: float(
                np.dot(target_centroids[c], src_centroid)
                / ((np.linalg.norm(target_centroids[c]) * np.linalg.norm(src_centroid)) + 1e-9)
            ),
        )
        labels[labels == smallest] = best
    return labels


def cluster_embeddings(
    embeddings: np.ndarray,
    student_ids: list[str],
    min_cluster_size: int = 3,
    min_cluster_fraction: float = 0.10,
) -> ClusteringResult:
    if len(student_ids) != embeddings.shape[0]:
        raise ValueError("student_ids and embeddings must have the same length")

    # MiniLM vectors live in high dimensions where density estimates are
    # unreliable for classroom-sized batches. Project down and re-normalize
    # before clustering (deterministic full-solver PCA).
    n_components = min(6, *embeddings.shape)
    reduced = normalize(
        PCA(n_components=n_components, svd_solver="full").fit_transform(embeddings)
    )

    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=1,
        metric="cosine",
        cluster_selection_method="eom",
    )
    raw_labels = clusterer.fit_predict(reduced)

    if min_cluster_fraction > 0 and len(student_ids) > 1:
        labels = merge_small_clusters(reduced, raw_labels, min_cluster_fraction)
    else:
        labels = raw_labels

    clusters = []
    for cluster_id in sorted(set(labels)):
        member_ids = [sid for sid, lbl in zip(student_ids, labels) if lbl == cluster_id]
        clusters.append(
            {
                "cluster_id": int(cluster_id),
                "student_ids": member_ids,
                "size": len(member_ids),
            }
        )
    # Largest first so downstream stages see the majority group at index 0;
    # noise stays last regardless of size.
    ordered = sorted(clusters, key=lambda c: (c["cluster_id"] == NOISE_CLUSTER_ID, -c["size"]))
    return ClusteringResult(labels=labels, clusters=ordered)


def run_stage3(records: list[dict], embeddings: np.ndarray) -> ClusteringResult:
    student_ids = [r["student_id"] for r in records]
    return cluster_embeddings(embeddings, student_ids)
