"""
Feature flag service wrapper for compatibility.
Imports from the actual location in features directory.
"""
import sys
import os

# Add parent directory to path to import from features
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.feature_flags import FeatureFlagService

__all__ = ['FeatureFlagService']