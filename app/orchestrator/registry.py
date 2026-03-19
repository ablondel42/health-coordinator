"""
Agent Registry Manager

Handles parsing and loading the raw JSON contracts that define agent behavior.
Provides a caching layer to avoid reading disk repetitively.
"""
import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Cache dictionary to hold parsed contracts
_CONTRACT_CACHE: Dict[str, Dict[str, Any]] = {}

def fetch_agent_registry_directory_path() -> str:
    """Calculate the absolute path to the agent-registry directory."""
    current_script_location = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_script_location, "..", "..", "agent-registry"))

def load_agent_contract_by_domain(domain_string: str) -> Dict[str, Any]:
    """
    Loads and parses an agent contract from disk or returns it from cache dynamically.
    
    Args:
        domain_string (str): The domain of the agent (e.g., 'documentation', 'code-quality').
        
    Returns:
        Dict[str, Any]: The fully parsed raw JSON contract dict.
        
    Raises:
        FileNotFoundError: If no contract matches the domain.
        ValueError: If the contract JSON is invalid.
    """
    if domain_string in _CONTRACT_CACHE:
        return _CONTRACT_CACHE[domain_string]
        
    core_registry_directory_path = fetch_agent_registry_directory_path()
    
    try:
        found_target_files = os.listdir(core_registry_directory_path)
        for valid_filename in found_target_files:
            if valid_filename.endswith(".contract.json"):
                absolute_file_path = os.path.join(core_registry_directory_path, valid_filename)
                with open(absolute_file_path, "r", encoding="utf-8") as file_handle:
                    extracted_contract_json = json.load(file_handle)
                    if extracted_contract_json.get("domain") == domain_string:
                        _CONTRACT_CACHE[domain_string] = extracted_contract_json
                        logger.info(f"Successfully loaded and cached contract for domain: {domain_string}")
                        return extracted_contract_json
    except Exception as general_read_error:
        logger.error(f"Failed processing registry at {core_registry_directory_path}", exc_info=general_read_error)
        raise RuntimeError(f"Could not read agent-registry bounds for {domain_string}") from general_read_error

    raise FileNotFoundError(f"No contract found in registry for domain '{domain_string}'.")

def list_all_registered_domains() -> list[str]:
    """Finds all valid .contract.json paths and dynamically extracts their native domain binds."""
    core_registry_directory_path = fetch_agent_registry_directory_path()
    resolved_domains_list = []
    
    try:
        found_target_files = os.listdir(core_registry_directory_path)
        for valid_filename in found_target_files:
            if valid_filename.endswith(".contract.json"):
                absolute_file_path = os.path.join(core_registry_directory_path, valid_filename)
                with open(absolute_file_path, "r", encoding="utf-8") as file_handle:
                    extracted_contract_json = json.load(file_handle)
                    domain_extracted = extracted_contract_json.get("domain")
                    if domain_extracted:
                        resolved_domains_list.append(domain_extracted)
    except Exception as generic_read_error:
        logger.error("Failed mapping complete agent-registry array list limits dynamically bounds natively cleanly mappings natively.", exc_info=generic_read_error)
        
    return resolved_domains_list
