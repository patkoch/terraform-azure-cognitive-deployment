# Azure model / region MCP server

A small [Model Context Protocol](https://modelcontextprotocol.io) server that
helps parameterize this repository's `terraform.auto.tfvars` with a valid
combination of Azure region and Azure OpenAI / Foundry model.

The server fetches the canonical Microsoft Learn page on demand and parses
the region/model support table:

<https://learn.microsoft.com/en-us/azure/foundry-classic/agents/concepts/model-region-support?tabs=global-standard>

If the page is unreachable, a small built-in fallback table is used (see
`FALLBACK_TABLE` in `server.py`); update it manually when adding a new
model.

## Tools

| Tool                          | Input                | Output                                                                 |
| ----------------------------- | -------------------- | ---------------------------------------------------------------------- |
| `list_regions_for_model`      | `model_name: str`    | Azure regions that support the model                                   |
| `list_models_for_region`      | `region: str`        | Models available in the region                                         |
| `get_recommended_tfvars`      | `model_name: str`    | Ready-to-paste `terraform.auto.tfvars` snippet (region + model + ver.) |

Each response includes a `source` field (`"live"` or `"fallback"`) and a
`reference` URL pointing back to the Microsoft Learn page.

## Install

```bash
cd mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run (stdio)

```bash
python server.py
```

## Register with an MCP-aware client

Example configuration snippet (e.g. for `~/.config/<client>/mcp.json`):

```json
{
  "mcpServers": {
    "azure-model-region": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-server/server.py"]
    }
  }
}
```

## Example session

```text
> list_regions_for_model("gpt-5")
{
  "model": "gpt-5",
  "regions": ["eastus2", "swedencentral"],
  "source": "live",
  "reference": "https://learn.microsoft.com/en-us/azure/foundry-classic/agents/concepts/model-region-support?tabs=global-standard"
}

> get_recommended_tfvars("gpt-5")
{
  "model": "gpt-5",
  "region": "eastus2",
  "model_version": "2025-08-07",
  "tfvars_snippet": "resource_group_name     = \"gpt-5-eastus2-rg\"\n..."
}
```
