#!/usr/bin/env python3
"""
Swagger/OpenAPI Filter and YAML Converter Script

This script filters a Swagger/OpenAPI JSON file based on endpoints listed in a text file,
includes all referenced schemas, and saves the result as a YAML file.

Usage:
    python swagger_filter.py
    
Required files:
    - swagger.json (your OpenAPI specification)
    - endpoints.txt (list of endpoints to filter, one per line)
    
Output:
    - filtered_swagger.yaml (filtered OpenAPI spec in YAML format)
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Any

def load_endpoints_from_file(file_path: str) -> List[str]:
    """Load endpoints from a text file, one per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            endpoints = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(endpoints)} endpoints from {file_path}")
        return endpoints
    except FileNotFoundError:
        print(f"Error: {file_path} not found!")
        return []

def load_swagger_json(file_path: str) -> Dict[str, Any]:
    """Load the Swagger/OpenAPI JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            swagger_data = json.load(f)
        print(f"Loaded Swagger file from {file_path}")
        return swagger_data
    except FileNotFoundError:
        print(f"Error: {file_path} not found!")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return {}

def extract_schema_references(obj: Any, refs: Set[str]) -> None:
    """Recursively extract all $ref schema references from an object."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == '$ref' and isinstance(value, str):
                # Extract schema name from reference like "#/components/schemas/SchemaName"
                if value.startswith('#/components/schemas/'):
                    schema_name = value.replace('#/components/schemas/', '')
                    refs.add(schema_name)
            else:
                extract_schema_references(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            extract_schema_references(item, refs)

def get_dependent_schemas(schema_name: str, all_schemas: Dict[str, Any], 
                         visited: Set[str] = None) -> Set[str]:
    """Recursively get all schemas that a given schema depends on."""
    if visited is None:
        visited = set()
    
    if schema_name in visited or schema_name not in all_schemas:
        return set()
    
    visited.add(schema_name)
    dependent_refs = set()
    
    # Extract references from this schema
    extract_schema_references(all_schemas[schema_name], dependent_refs)
    
    # Recursively get dependencies of dependencies
    all_deps = dependent_refs.copy()
    for dep in dependent_refs:
        all_deps.update(get_dependent_schemas(dep, all_schemas, visited.copy()))
    
    return all_deps

def filter_swagger_by_endpoints(swagger_data: Dict[str, Any], 
                               target_endpoints: List[str]) -> Dict[str, Any]:
    """Filter Swagger data to include only specified endpoints and their schemas."""
    
    # Create filtered swagger structure
    filtered_swagger = {
        'openapi': swagger_data.get('openapi', '3.0.1'),
        'info': swagger_data.get('info', {}),
        'servers': swagger_data.get('servers', []),
        'tags': swagger_data.get('tags', []),
        'paths': {},
        'components': {
            'schemas': {}
        }
    }
    
    # Get original paths and components
    original_paths = swagger_data.get('paths', {})
    original_schemas = swagger_data.get('components', {}).get('schemas', {})
    
    # Track all schema references we need
    required_schemas = set()
    matched_endpoints = []
    
    # Filter paths based on target endpoints
    for endpoint in target_endpoints:
        # Clean endpoint format (remove leading/trailing slashes, spaces)
        clean_endpoint = endpoint.strip().strip('/')
        
        # Try to match endpoints (exact match and flexible matching)
        for path, path_data in original_paths.items():
            clean_path = path.strip().strip('/')
            
            # Exact match or contains match
            if (clean_endpoint == clean_path or 
                clean_endpoint in clean_path or 
                clean_path.endswith(clean_endpoint)):
                
                filtered_swagger['paths'][path] = path_data
                matched_endpoints.append(endpoint)
                
                # Extract schema references from this path
                extract_schema_references(path_data, required_schemas)
                break
    
    print(f"Matched {len(matched_endpoints)} endpoints:")
    for endpoint in matched_endpoints:
        print(f"  - {endpoint}")
    
    if len(matched_endpoints) != len(target_endpoints):
        unmatched = set(target_endpoints) - set(matched_endpoints)
        print(f"Unmatched endpoints ({len(unmatched)}):")
        for endpoint in unmatched:
            print(f"  - {endpoint}")
    
    # Get all dependent schemas recursively
    all_required_schemas = set()
    for schema_name in required_schemas:
        all_required_schemas.add(schema_name)
        all_required_schemas.update(get_dependent_schemas(schema_name, original_schemas))
    
    # Add required schemas to filtered swagger
    for schema_name in all_required_schemas:
        if schema_name in original_schemas:
            filtered_swagger['components']['schemas'][schema_name] = original_schemas[schema_name]
    
    print(f"Included {len(all_required_schemas)} schemas:")
    for schema in sorted(all_required_schemas):
        print(f"  - {schema}")
    
    return filtered_swagger

def save_as_yaml(data: Dict[str, Any], output_file: str) -> None:
    """Save dictionary data as YAML file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, 
                     allow_unicode=True, indent=2)
        print(f"Filtered Swagger saved as {output_file}")
    except Exception as e:
        print(f"Error saving YAML file: {e}")

def print_summary(filtered_data: Dict[str, Any]) -> None:
    """Print a summary of the filtered Swagger file."""
    print("\n" + "="*50)
    print("FILTERED SWAGGER SUMMARY")
    print("="*50)
    
    paths = filtered_data.get('paths', {})
    schemas = filtered_data.get('components', {}).get('schemas', {})
    
    print(f"Total Endpoints: {len(paths)}")
    print(f"Total Schemas: {len(schemas)}")
    
    if paths:
        print(f"\nEndpoints included:")
        for i, path in enumerate(paths.keys(), 1):
            methods = list(paths[path].keys())
            print(f"  {i}. {path} [{', '.join(methods).upper()}]")
    
    if schemas:
        print(f"\nSchemas included:")
        for i, schema in enumerate(sorted(schemas.keys()), 1):
            print(f"  {i}. {schema}")

def main():
    """Main function to execute the filtering process."""
    print("Swagger/OpenAPI Filter and YAML Converter")
    print("="*50)
    
    # File paths
    endpoints_file = "./tests/allowed_endpoints2.txt"
    swagger_file = "./tests/byanati_new.json"
    output_file = "./tests/filtered_swagger22.yaml"
    
    # Check if files exist
    if not Path(endpoints_file).exists():
        print(f"Creating sample {endpoints_file} file...")
        sample_endpoints = [
            "/api/MobileAPI/VALIDATE_USER_LOGIN",
            "/api/MobileAPI/GET_ATTACHMENT_BY_KEY",
            "/api/MobileAPI/ADD_ATTACHMENT"
        ]
        with open(endpoints_file, 'w') as f:
            f.write('\n'.join(sample_endpoints))
        print(f"Sample {endpoints_file} created. Please edit it with your endpoints.")
        return
    
    if not Path(swagger_file).exists():
        print(f"Error: {swagger_file} not found!")
        print("Please place your Swagger/OpenAPI JSON file as 'swagger.json'")
        return
    
    # Load data
    target_endpoints = load_endpoints_from_file(endpoints_file)
    swagger_data = load_swagger_json(swagger_file)
    
    if not target_endpoints or not swagger_data:
        print("Error: Could not load required files.")
        return
    
    # Filter swagger data
    print(f"\nFiltering Swagger file...")
    filtered_data = filter_swagger_by_endpoints(swagger_data, target_endpoints)
    
    # Save as YAML
    save_as_yaml(filtered_data, output_file)
    
    # Print summary
    print_summary(filtered_data)
    
    print(f"\n✅ Process completed successfully!")
    print(f"📁 Output file: {output_file}")

if __name__ == "__main__":
    main()