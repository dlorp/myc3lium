#!/usr/bin/env python3
"""
OpenClaw Semantic Pattern Clustering
Uses lightweight sentence embeddings (all-MiniLM-L6-v2) to find similar patterns.
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

# Check if sentence-transformers available
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("Warning: sentence-transformers not installed")
    print("Install with: pip install sentence-transformers")

MEMORY_DIR = Path(__file__).parent
EMBEDDINGS_CACHE = MEMORY_DIR / "embeddings-cache.json"

class PatternClusterer:
    def __init__(self):
        if not HAS_EMBEDDINGS:
            raise RuntimeError("sentence-transformers not available")
        
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load embedding cache to avoid recomputing."""
        if EMBEDDINGS_CACHE.exists():
            with open(EMBEDDINGS_CACHE) as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save embedding cache."""
        with open(EMBEDDINGS_CACHE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def embed(self, texts):
        """Generate embeddings for texts (with caching)."""
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            if text in self.cache:
                embeddings.append(self.cache[text])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                embeddings.append(None)
        
        # Compute uncached embeddings
        if uncached_texts:
            print(f"  Computing embeddings for {len(uncached_texts)} new texts...")
            new_embeddings = self.model.encode(uncached_texts)
            
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embeddings[idx] = embedding.tolist()
                self.cache[texts[idx]] = embedding.tolist()
            
            self._save_cache()
        
        return np.array(embeddings)
    
    def cluster_patterns(self, patterns, eps=0.3, min_samples=2):
        """
        Cluster patterns using DBSCAN on embeddings.
        eps: Maximum distance between samples to be in same cluster (0.3 = ~70% similarity)
        min_samples: Minimum cluster size
        """
        print(f"\nClustering {len(patterns)} patterns...")
        
        # Get embeddings
        embeddings = self.embed(patterns)
        
        # Compute pairwise cosine similarity
        similarities = cosine_similarity(embeddings)
        
        # Convert to distance (1 - similarity)
        distances = 1 - similarities
        
        # Cluster with DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        labels = clustering.fit_predict(distances)
        
        # Group by cluster
        clusters = {}
        noise = []
        
        for i, label in enumerate(labels):
            if label == -1:
                noise.append(patterns[i])
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(patterns[i])
        
        print(f"  Found {len(clusters)} clusters, {len(noise)} noise points")
        
        return clusters, noise
    
    def find_similar(self, query, candidates, top_k=5, threshold=0.7):
        """Find top-k most similar candidates to query."""
        all_texts = [query] + candidates
        embeddings = self.embed(all_texts)
        
        query_emb = embeddings[0].reshape(1, -1)
        candidate_embs = embeddings[1:]
        
        similarities = cosine_similarity(query_emb, candidate_embs)[0]
        
        # Filter by threshold and sort
        results = [(candidates[i], similarities[i]) 
                   for i in range(len(candidates)) 
                   if similarities[i] >= threshold]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]

def load_patterns_from_discord():
    """Load patterns from #patterns channel (placeholder - would need Discord integration)."""
    # TODO: Integrate with Discord message tool to read #patterns channel
    # For now, return example patterns
    return [
        "Build complementary tool pairs (historical + real-time)",
        "Constraints breed creativity - embrace limitations",
        "Procedural generation needs domain constraints",
        "Terminal-native tools over GUI for iteration speed",
        "Local-first approach for simplicity",
        "Don't build monoliths, build focused pairs",
        "Ecosystem building > random one-offs",
        "Each tool reinforces others in complete pipeline"
    ]

def main():
    """Run pattern clustering analysis."""
    if not HAS_EMBEDDINGS:
        print("Error: sentence-transformers not installed")
        print("Install with: pip install sentence-transformers")
        return
    
    clusterer = PatternClusterer()
    
    # Load patterns
    patterns = load_patterns_from_discord()
    print(f"Loaded {len(patterns)} patterns from #patterns channel")
    
    # Cluster
    clusters, noise = clusterer.cluster_patterns(patterns, eps=0.4, min_samples=2)
    
    # Display results
    print("\n" + "=" * 70)
    print("PATTERN CLUSTERS")
    print("=" * 70)
    
    for cluster_id, cluster_patterns in clusters.items():
        print(f"\nCluster {cluster_id} ({len(cluster_patterns)} patterns):")
        for pattern in cluster_patterns:
            print(f"  • {pattern}")
    
    if noise:
        print(f"\nUnclustered ({len(noise)} patterns):")
        for pattern in noise:
            print(f"  • {pattern}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    # Suggest axiom candidates from large clusters
    for cluster_id, cluster_patterns in clusters.items():
        if len(cluster_patterns) >= 3:
            print(f"\n✓ Cluster {cluster_id} has {len(cluster_patterns)} related patterns")
            print("  → Candidate for new AXIOM (recurring theme)")
            print(f"  Theme: {cluster_patterns[0]}")

if __name__ == '__main__':
    main()
