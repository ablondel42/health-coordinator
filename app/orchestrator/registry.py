"""
Agent Registry Manager

Loads and caches agent contract JSON files from the agent-registry directory.
"""
import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

_contract_cache: Dict[str, Dict[str, Any]] = {}


def get_registry_path() -> str:
    """Return the absolute path to the agent-registry directory."""
    current_file = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_file, "..", "..", "agent-registry"))


def load_contract(domain: str) -> Dict[str, Any]:
    """
    Load an agent contract from disk or cache.

    Args:
        domain: The agent domain (e.g., 'documentation', 'code-quality').

    Returns:
        The parsed contract JSON.

    Raises:
        FileNotFoundError: If no contract exists for the domain.
    """
    if domain in _contract_cache:
        return _contract_cache[domain]

    registry_path = get_registry_path()

    try:
        files = os.listdir(registry_path)
        for filename in files:
            if filename.endswith(".contract.json"):
                filepath = os.path.join(registry_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    contract = json.load(f)
                    if contract.get("domain") == domain:
                        _contract_cache[domain] = contract
                        logger.info(f"Loaded contract for domain: {domain}")
                        return contract
    except Exception as e:
        logger.error(f"Failed to read registry at {registry_path}", exc_info=e)
        raise RuntimeError(f"Could not read agent registry for domain '{domain}'") from e

    raise FileNotFoundError(f"No contract found for domain '{domain}'")


def list_domains() -> list[str]:
    """Return a list of all registered agent domains."""
    registry_path = get_registry_path()
    domains = []

    try:
        files = os.listdir(registry_path)
        for filename in files:
            if filename.endswith(".contract.json"):
                filepath = os.path.join(registry_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    contract = json.load(f)
                    domain = contract.get("domain")
                    if domain:
                        domains.append(domain)
    except Exception as e:
        logger.error("Failed to read agent registry", exc_info=e)

    return domains
