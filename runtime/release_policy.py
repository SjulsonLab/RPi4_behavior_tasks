from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleasePolicy:
    allowed_release_branches: tuple[str, ...] = ("main", "release")
    allowed_release_branch_prefixes: tuple[str, ...] = ("release/",)
    allowed_release_tag_prefixes: tuple[str, ...] = ("v", "release-")
    require_clean_tree_in_production: bool = True


DEFAULT_RELEASE_POLICY = ReleasePolicy()
