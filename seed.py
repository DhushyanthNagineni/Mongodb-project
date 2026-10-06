"""Seed script: Populates initial administrator account and curated technical articles.

Run from Anaconda Python:
    python seed.py
"""
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

import db

load_dotenv()

USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def ensure_admin():
    existing = db.get_admin(USERNAME)
    if existing:
        return
    db.admin_collection().insert_one({
        "username": USERNAME,
        "password_hash": generate_password_hash(PASSWORD),
    })
    print(f"Created administrator '{USERNAME}'.")


def sample_posts():
    # Only insert if no posts exist
    if db.posts_collection().count_documents({}) > 0:
        return

    base = datetime.utcnow()
    samples = [
        {
            "title": "Decoupled Architecture: Designing Resilient Event-Driven Systems",
            "slug": "decoupled-architecture-resilient-event-driven-systems",
            "category": "Systems",
            "tags": ["distributed-systems", "architecture", "concurrency"],
            "body": (
                "## The Shift Toward Event Sourcing\n\n"
                "In traditional synchronous architectures, service boundaries often mask deep coupling. "
                "When a downstream dependency encounters transient latency, call stacks block, connection pools "
                "exhaust, and cascading failures ripple across the boundary.\n\n"
                "> A decoupled system does not eliminate failure; it ensures failures remain localized, "
                "observable, and gracefully recoverable.\n\n"
                "### Architectural Trade-offs\n\n"
                "When evaluating event streams against traditional RPC boundaries, several invariants must be preserved:\n\n"
                "- **Idempotency**: Processing workers must safely handle duplicate delivery without state corruption.\n"
                "- **Ordering guarantees**: Partitioning keys must align with entity lifecycles to prevent out-of-order mutations.\n"
                "- **Replayability**: The event store serves as the immutable source of truth, enabling deterministic audits.\n\n"
                "```python\n"
                "class EventEnvelope:\n"
                "    def __init__(self, aggregate_id: str, sequence: int, payload: dict):\n"
                "        self.aggregate_id = aggregate_id\n"
                "        self.sequence = sequence\n"
                "        self.payload = payload\n"
                "        self.timestamp = datetime.utcnow()\n\n"
                "    def apply_to(self, state: dict) -> dict:\n"
                "        # Deterministic state reduction\n"
                "        return {**state, **self.payload, 'version': self.sequence}\n"
                "```\n\n"
                "### Protocol Comparison\n\n"
                "| Dimension | Synchronous RPC | Event Streaming |\n"
                "| :--- | :--- | :--- |\n"
                "| Latency Profile | Immediate round-trip | Asynchronous, buffered |\n"
                "| Fault Isolation | Tight coupling | Complete queue decoupling |\n"
                "| State Recovery | Point-in-time snapshots | Continuous event replay |\n\n"
                "By decoupling write ingestion from read projection, applications maintain predictable p99 latency "
                "even under aggressive traffic spikes."
            ),
            "author": USERNAME,
            "is_published": True,
        },
        {
            "title": "The Anatomy of Latency: Memory Hierarchy and Cache Locality",
            "slug": "anatomy-of-latency-memory-hierarchy-cache-locality",
            "category": "Performance",
            "tags": ["performance", "low-level", "optimization"],
            "body": (
                "## Beyond Big-O Complexity\n\n"
                "Algorithmic complexity often blinds engineers to mechanical sympathy. An algorithm with $O(N)$ "
                "traversal over contiguous memory frequently outperforms an $O(\\log N)$ structure traversing pointer-chased heap nodes.\n\n"
                "### The Memory Wall\n\n"
                "Access latencies across modern CPU tiers diverge by orders of magnitude:\n\n"
                "1. **L1 Cache**: ~1 nanosecond (4 cycles)\n"
                "2. **L2 Cache**: ~3-4 nanoseconds (12 cycles)\n"
                "3. **L3 Cache**: ~10-15 nanoseconds (40 cycles)\n"
                "4. **Main Memory (DRAM)**: ~60-80 nanoseconds (200+ cycles)\n\n"
                "```c\n"
                "// Cache-friendly struct-of-arrays approach\n"
                "struct TransformMatrix {\n"
                "    float x[MAX_ENTITIES];\n"
                "    float y[MAX_ENTITIES];\n"
                "    float z[MAX_ENTITIES];\n"
                "};\n"
                "```\n\n"
                "Structuring data for sequential SIMD vectorization prevents prefetcher stalls and sustains near-theoretical throughput."
            ),
            "author": USERNAME,
            "is_published": True,
        },
        {
            "title": "Consensus Invariants: Linearizability in Distributed Datastores",
            "slug": "consensus-invariants-linearizability-distributed-datastores",
            "category": "Databases",
            "tags": ["consensus", "raft", "storage"],
            "body": (
                "## Formulating Correctness Under Partitions\n\n"
                "Linearizability provides the illusion that a distributed system acts as a single centralized entity. "
                "Achieving this requires strict lease coordination and deterministic log replication protocols.\n\n"
                "### Quorum Intersection\n\n"
                "In a cluster of $2F + 1$ nodes, any majority quorum of size $F + 1$ is guaranteed to overlap with "
                "every other majority quorum by at least one node, ensuring uncommitted entries cannot survive leader reelection."
            ),
            "author": USERNAME,
            "is_published": True,
        },
        {
            "title": "Internal Notes on Distributed Cache Invalidation Strategies",
            "slug": "internal-notes-distributed-cache-invalidation",
            "category": "Engineering",
            "tags": ["caching", "internal"],
            "body": (
                "## Private Draft: Operational Patterns\n\n"
                "This document summarizes upcoming migration strategies for lease-based cache invalidation.\n\n"
                "- Two-phase invalidation locks\n"
                "- Probabilistic early expiration algorithms (XFetch)\n"
                "- Write-through versus write-around pipelines"
            ),
            "author": USERNAME,
            "is_published": False,
        },
    ]

    for i, sample in enumerate(samples):
        created = base - timedelta(days=i * 2)
        sample["created_at"] = created
        sample["updated_at"] = created
        db.create_post(sample)

    print(f"Inserted {len(samples)} curated articles.")


if __name__ == "__main__":
    ensure_admin()
    sample_posts()
