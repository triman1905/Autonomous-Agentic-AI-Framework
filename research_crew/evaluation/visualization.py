"""
visualization.py
----------------
Creates a clean quality improvement graph (no stage labels)
"""

import matplotlib.pyplot as plt
from pathlib import Path


def plot_quality_graph(scores):
    if not scores:
        return

    # Ensure output directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    iterations = list(range(1, len(scores) + 1))

    plt.figure(figsize=(8, 5))

    # Line plot
    plt.plot(iterations, scores, marker='o')

    # Titles and labels (aligned with your project terminology)
    plt.title("Quality Score Progression")
    plt.xlabel("Iteration Number")
    plt.ylabel("Quality Score")   # ✅ fixed (was Performance Score)

    # Legend
    plt.legend(["Agentic Workflow"])

    # Grid
    plt.grid(True)

    # Numeric annotations only (clean)
    for x, y in zip(iterations, scores):
        plt.text(x, y + 0.5, str(y), ha='center')  # ✅ better spacing

    # Save graph
    path = output_dir / "quality_graph.png"
    plt.savefig(path, bbox_inches='tight')  # ✅ prevents clipping
    plt.close()

    print(f"📈 Graph saved → {path}")