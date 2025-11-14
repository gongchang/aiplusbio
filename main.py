"""Cloud Function entrypoint module.

This file keeps the Cloud Function deployment simple by exposing a
`scrape_http` function at module scope.  We lazily import the Cloud
Function implementation so that local tooling that imports `main`
does not pay the cost of importing heavy scraper dependencies unless
it's actually needed.
"""

from __future__ import annotations

import importlib
from typing import Any


def scrape_http(*args: Any, **kwargs: Any):
    """Delegate Cloud Function HTTP requests to the scraper handler."""
    module = importlib.import_module('cloud_functions.scrape_http')
    handler = getattr(module, 'scrape_http')
    return handler(*args, **kwargs)
