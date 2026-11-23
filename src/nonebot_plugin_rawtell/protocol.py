"""Data models shared across rAwTell submodules.

Keep contracts here rather than passing ad-hoc dicts between submodules. Add a
Pydantic model per cross-module payload (config-independent), and keep
timestamps timezone-aware UTC.
"""
