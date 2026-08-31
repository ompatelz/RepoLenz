"""Consistent package logging without configuring root logging on import."""

from __future__ import annotations

import logging


def configure_logging(verbose: bool = False) -> None:
    """Configure RepoLens console logs when called by an executable entry point."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
