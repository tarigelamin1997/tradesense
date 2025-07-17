"""
Feature flag service wrapper for compatibility.
Imports from the actual location in features directory.
"""
from features.feature_flags import FeatureFlagService

__all__ = ['FeatureFlagService']