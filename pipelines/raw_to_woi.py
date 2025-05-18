#!/usr/bin/env python3
"""
pipelines/raw_filter_to_woi.py

Pipeline entrypoint: repopulates woi.db by running the filtered WoI pipeline.
"""

import asyncio
import os
import sys

# ────────────────────────────────────────────────────────────────────
# Compute project root (one level up from pipelines/)
# ────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(__file__)                     # .../your-project/pipelines
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

# Now import from data.woi_data
from data.woi_data import populate_filtered_woi

if __name__ == "__main__":
    # Adjust top_percent if you like
    asyncio.run(populate_filtered_woi(top_percent=10))
