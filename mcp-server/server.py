"""Azure OpenAI model/region MCP server.

This MCP server exposes three tools that help parameterize the Terraform
configuration in this repository (`terraform.auto.tfvars`) with a valid
combination of Azure region and Azure OpenAI / Foundry model.

The canonical source of truth is the Microsoft Learn page:
  https://learn.microsoft.com/en-us/azure/foundry-classic/agents/concepts/model-region-support?tabs=global-standard

The server fetches and parses that page on demand, caches the result for
``CACHE_TTL_SECONDS``, and exposes the parsed table through three tools:

* ``list_regions_for_model(model_name)`` - regions that support the model
* ``list_models_for_region(region)``     - models available in the region
* ``get_recommended_tfvars(model_name)`` - ready-to-paste tfvars snippet

A small built-in fallback table (``FALLBACK_TABLE``) is used if the live
Microsoft Learn page is unreachable (e.g. from a sandboxed CI runner). The
fallback only covers the models that this repository is most likely to
deploy and must be kept up to date manually.

Run as an MCP server over stdio:

    python -m pip install -r requirements.txt
    python server.py
"""

from __future__ import annotations

import html
import json
import logging
import re
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - import guard for clearer error
    raise SystemExit(
        "The 'mcp' package is required. Install it with: "
        "pip install -r requirements.txt"
    ) from exc


MS_LEARN_URL = (
    "https://learn.microsoft.com/en-us/azure/foundry-classic/agents/"
    "concepts/model-region-support?tabs=global-standard"
)

CACHE_TTL_SECONDS = 60 * 60  # 1 hour

# Manually curated fallback used when the Microsoft Learn page cannot be
# fetched. Keys are lower-cased model names, values are the list of regions
# (Azure region short names as accepted by the Azure CLI / Terraform) that
# support the model on the "Global Standard" deployment SKU. Update when
# adding support for a new model.
FALLBACK_TABLE: dict[str, list[str]] = {
    "gpt-5": ["eastus2", "swedencentral"],
    "gpt-5-mini": ["eastus2", "swedencentral"],
    "gpt-5-nano": ["eastus2", "swedencentral"],
    "gpt-4.1": ["eastus2", "swedencentral"],
    "gpt-4o": ["eastus", "eastus2", "swedencentral", "westus", "westus3"],
    "gpt-4o-mini": ["eastus", "eastus2", "swedencentral", "westus", "westus3"],
}

# Recommended pin per model. The Microsoft Learn page lists the currently
# supported model version(s); when fallback is used we provide the version
# known to be GA at the time of writing.
FALLBACK_MODEL_VERSION: dict[str, str] = {
    "gpt-5": "2025-08-07",
    "gpt-5-mini": "2025-08-07",
    "gpt-5-nano": "2025-08-07",
    "gpt-4.1": "2025-04-14",
    "gpt-4o": "2024-11-20",
    "gpt-4o-mini": "2024-07-18",
}

logger = logging.getLogger("azure-model-region-mcp")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


@dataclass
class CacheEntry:
    fetched_at: float
    table: dict[str, list[str]]
    source: str  # "live" or "fallback"


_cache: CacheEntry | None = None


def _strip_html(value: str) -> str:
    """Return the text content of an HTML fragment."""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_key(value: str) -> str:
    """Normalize model/region keys for lookups."""
    return _strip_html(value).lower()


def _normalize_region(value: str) -> str:
    """Normalize a region name to a Terraform/Azure-friendly token."""
    return _normalize_key(value).replace(" ", "")


def _base_model_name(model_name: str) -> str:
    """Return model name without trailing parenthesized version suffix."""
    base = re.sub(r"\s*\([^)]*\)\s*$", "", model_name)
    return re.sub(r"\s+", " ", base).strip().lower()


def _cell_indicates_support(cell: str) -> bool:
    """Return True if the table cell indicates regional support."""
    marker = _normalize_key(cell)
    if not marker:
        return False
    return marker not in {"-", "--", "n/a", "na", "no", "not available", "❌", "x"}


def _parse_region_model_table(page_html: str) -> dict[str, list[str]]:
    """Parse the Microsoft Learn region/model table.

    The page renders a table with the model name as the first column and
    one column per region. A cell is non-empty when the region supports
    the model. We extract a normalized ``{model_name: [region, ...]}``
    mapping from that table.

    The function tolerates small markup changes by looking for the first
    ``<table>`` that contains both the strings "Model" and known region
    names (e.g. ``swedencentral`` or ``East US``).
    """
    tables = re.findall(r"<table[^>]*>.*?</table>", page_html, flags=re.IGNORECASE | re.DOTALL)
    merged: dict[str, set[str]] = {}
    for table_html in tables:
        if "swedencentral" not in table_html.lower() and "sweden central" not in table_html.lower():
            continue

        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, flags=re.IGNORECASE | re.DOTALL)
        if not rows:
            continue

        matrix: list[list[str]] = []
        for row_html in rows:
            cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row_html, flags=re.IGNORECASE | re.DOTALL)
            if cells:
                matrix.append([_strip_html(c) for c in cells])

        if len(matrix) < 2:
            continue

        headers = matrix[0]
        first_header = _normalize_key(headers[0])

        # Current Learn markup is usually region-first: Region | gpt-5 | gpt-4o ...
        if first_header in {"region", "regions"}:
            model_headers = [_normalize_key(h) for h in headers[1:]]
            for row in matrix[1:]:
                if len(row) < 2:
                    continue
                region = _normalize_region(row[0])
                if not region:
                    continue
                for model_name, cell in zip(model_headers, row[1:]):
                    if not model_name or not _cell_indicates_support(cell):
                        continue
                    merged.setdefault(model_name, set()).add(region)
            continue

        # Backward compatibility: model-first table layout.
        if first_header in {"model", "models"}:
            region_headers = [_normalize_region(h) for h in headers[1:]]
            for row in matrix[1:]:
                if len(row) < 2:
                    continue
                model_name = _normalize_key(row[0])
                if not model_name:
                    continue
                for region, cell in zip(region_headers, row[1:]):
                    if not region or not _cell_indicates_support(cell):
                        continue
                    merged.setdefault(model_name, set()).add(region)

    if merged:
        return {model: sorted(regions) for model, regions in merged.items()}
    raise ValueError("Could not locate the region/model table on the page")


def _regions_for_model(table: dict[str, list[str]], model_name: str) -> list[str]:
    """Resolve regions for a model, including versioned model-name variants."""
    key = model_name.strip().lower()
    regions = table.get(key, [])
    if regions:
        return regions

    base = _base_model_name(key)
    merged: set[str] = set()
    for candidate, candidate_regions in table.items():
        if _base_model_name(candidate) == base:
            merged.update(candidate_regions)
    return sorted(merged)


def _fetch_live_table() -> dict[str, list[str]]:
    req = urllib.request.Request(
        MS_LEARN_URL,
        headers={"User-Agent": "azure-model-region-mcp/0.1 (+terraform-azure-cognitive-deployment)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - public docs URL
        page_html = resp.read().decode("utf-8", errors="replace")
    return _parse_region_model_table(page_html)


def _get_table() -> CacheEntry:
    global _cache
    now = time.time()
    if _cache is not None and (now - _cache.fetched_at) < CACHE_TTL_SECONDS:
        return _cache
    try:
        table = _fetch_live_table()
        _cache = CacheEntry(fetched_at=now, table=table, source="live")
        logger.info("Loaded region/model table from Microsoft Learn (%d models)", len(table))
    except Exception as exc:  # pragma: no cover - network errors are environment-specific
        logger.warning("Falling back to built-in table: %s", exc)
        _cache = CacheEntry(fetched_at=now, table=dict(FALLBACK_TABLE), source="fallback")
    return _cache


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------


mcp = FastMCP("azure-model-region")


@mcp.tool()
def list_regions_for_model(model_name: str) -> dict[str, Any]:
    """Return the Azure regions that support the given Azure OpenAI/Foundry model.

    Args:
        model_name: Model name as it appears on the Microsoft Learn page,
            e.g. ``gpt-5``, ``gpt-4o``, ``gpt-4.1``.

    Returns:
        A mapping with ``model``, ``regions`` and ``source`` keys. ``source``
        is ``"live"`` when the data was just retrieved from Microsoft Learn,
        or ``"fallback"`` when the built-in static table was used.
    """
    entry = _get_table()
    regions = _regions_for_model(entry.table, model_name)
    return {
        "model": model_name,
        "regions": regions,
        "source": entry.source,
        "reference": MS_LEARN_URL,
    }


@mcp.tool()
def list_models_for_region(region: str) -> dict[str, Any]:
    """Return all Azure OpenAI/Foundry models supported in the given region.

    Args:
        region: Azure region short name (e.g. ``swedencentral``, ``eastus2``)
            or the human-readable name shown on Microsoft Learn (e.g.
            ``Sweden Central``). The comparison is case-insensitive and
            ignores whitespace.

    Returns:
        A mapping with ``region``, ``models`` and ``source`` keys.
    """
    entry = _get_table()
    needle = region.strip().lower().replace(" ", "")
    models = sorted(
        model
        for model, regions in entry.table.items()
        if any(r.lower().replace(" ", "") == needle for r in regions)
    )
    return {
        "region": region,
        "models": models,
        "source": entry.source,
        "reference": MS_LEARN_URL,
    }


@mcp.tool()
def get_recommended_tfvars(model_name: str) -> dict[str, Any]:
    """Suggest values for ``terraform.auto.tfvars`` to deploy the given model.

    The recommendation picks the *first* supported region returned for the
    model (Microsoft Learn orders regions deterministically) and pairs it
    with the GA model version known to this server. The result is intended
    to be pasted into this repository's ``terraform.auto.tfvars``.

    Args:
        model_name: Azure OpenAI/Foundry model name (e.g. ``gpt-5``).

    Returns:
        A mapping with ``model``, ``region``, ``model_version``, a ready-to-
        paste ``tfvars`` snippet and the data ``source``.
    """
    entry = _get_table()
    key = model_name.strip().lower()
    regions = _regions_for_model(entry.table, model_name)
    if not regions:
        return {
            "model": model_name,
            "error": f"Model '{model_name}' not found in region/model table",
            "reference": MS_LEARN_URL,
            "source": entry.source,
        }

    region = regions[0]
    region_slug = re.sub(r"[^a-z0-9]+", "-", region.lower()).strip("-")
    model_slug = re.sub(r"[^a-z0-9]+", "-", model_name.lower()).strip("-")
    model_version = FALLBACK_MODEL_VERSION.get(key, "")

    snippet = (
        f'resource_group_name     = "{model_slug}-{region_slug}-rg"\n'
        f'resource_group_location = "{region}"\n'
        f'\n'
        f'cognitive_account_name                  = "{model_slug}-{region_slug}-ca"\n'
        f'cognitive_account_custom_subdomain_name = "{model_slug}-{region_slug}"\n'
        f'\n'
        f'cognitive_deployment_name          = "{model_slug}-{region_slug}-cd"\n'
        f'cognitive_deployment_model_format  = "OpenAI"\n'
        f'cognitive_deployment_model_name    = "{model_name}"\n'
        f'cognitive_deployment_model_version = "{model_version}"\n'
        f'cognitive_deployment_sku_name      = "GlobalStandard"\n'
        f'cognitive_deployment_sku_capacity  = 45\n'
    )

    return {
        "model": model_name,
        "region": region,
        "model_version": model_version,
        "tfvars_snippet": snippet,
        "source": entry.source,
        "reference": MS_LEARN_URL,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
