import yaml
import json
import re
from typing import Set, Dict, Any

def load_swagger(file_path):
    with open(file_path, 'r') as f:
        if file_path.endswith(('.yaml', '.yml')):
            return yaml.safe_load(f)
        elif file_path.endswith('.json'):
            return json.load(f)
        else:
            raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")

def save_swagger(swagger_data, file_path):
    with open(file_path, 'w') as f:
        if file_path.endswith(('.yaml', '.yml')):
            yaml.dump(swagger_data, f, sort_keys=False)
        elif file_path.endswith('.json'):
            json.dump(swagger_data, f, indent=2)
        else:
            raise ValueError("Unsupported output file format.")

def load_allowed_endpoints(txt_file):
    with open(txt_file, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def find_schema_references(obj: Any, references: Set[str] = None) -> Set[str]:
    """
    Recursively find all schema references in a JSON/YAML object.
    Looks for $ref patterns like "#/components/schemas/SchemaName"
    """
    if references is None:
        references = set()
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == '$ref' and isinstance(value, str):
                # Extract schema name from reference
                if '#/components/schemas/' in value:
                    schema_name = value.split('#/components/schemas/')[-1]
                    references.add(schema_name)
                elif '#/definitions/' in value:  # OpenAPI 2.0 format
                    schema_name = value.split('#/definitions/')[-1]
                    references.add(schema_name)
            else:
                find_schema_references(value, references)
    elif isinstance(obj, list):
        for item in obj:
            find_schema_references(item, references)
    
    return references

def find_referenced_schemas(swagger_data: Dict[str, Any], filtered_paths: Dict[str, Any]) -> Set[str]:
    """
    Find all schemas referenced by the filtered endpoints and their dependencies.
    """
    referenced_schemas = set()
    
    # Find direct references from filtered paths
    direct_refs = find_schema_references(filtered_paths)
    referenced_schemas.update(direct_refs)
    
    # Find transitive references (schemas referenced by other schemas)
    schemas_section = swagger_data.get('components', {}).get('schemas', {})
    if not schemas_section:
        schemas_section = swagger_data.get('definitions', {})  # OpenAPI 2.0
    
    # Keep adding referenced schemas until no new ones are found
    prev_size = 0
    while len(referenced_schemas) != prev_size:
        prev_size = len(referenced_schemas)
        schemas_to_check = referenced_schemas.copy()
        
        for schema_name in schemas_to_check:
            if schema_name in schemas_section:
                schema_def = schemas_section[schema_name]
                nested_refs = find_schema_references(schema_def)
                referenced_schemas.update(nested_refs)
    
    return referenced_schemas

def filter_swagger_with_schemas(swagger_data: Dict[str, Any], allowed_paths: Set[str]) -> Dict[str, Any]:
    """
    Filter swagger data to keep only allowed paths and their referenced schemas.
    """
    # Filter paths
    all_paths = swagger_data.get('paths', {})
    filtered_paths = {
        path: details for path, details in all_paths.items()
        if path in allowed_paths
    }
    swagger_data['paths'] = filtered_paths
    
    # Find schemas referenced by filtered paths
    referenced_schemas = find_referenced_schemas(swagger_data, filtered_paths)
    
    # Filter schemas in components (OpenAPI 3.0+)
    if 'components' in swagger_data and 'schemas' in swagger_data['components']:
        original_schemas = swagger_data['components']['schemas']
        filtered_schemas = {
            name: schema for name, schema in original_schemas.items()
            if name in referenced_schemas
        }
        swagger_data['components']['schemas'] = filtered_schemas
        
        print(f"Schemas: {len(original_schemas)} -> {len(filtered_schemas)} "
              f"(removed {len(original_schemas) - len(filtered_schemas)})")
    
    # Filter definitions (OpenAPI 2.0)
    if 'definitions' in swagger_data:
        original_definitions = swagger_data['definitions']
        filtered_definitions = {
            name: definition for name, definition in original_definitions.items()
            if name in referenced_schemas
        }
        swagger_data['definitions'] = filtered_definitions
        
        print(f"Definitions: {len(original_definitions)} -> {len(filtered_definitions)} "
              f"(removed {len(original_definitions) - len(filtered_definitions)})")
    
    return swagger_data

def filter_swagger(swagger_data, allowed_paths):
    """Legacy function for backward compatibility"""
    return filter_swagger_with_schemas(swagger_data, allowed_paths)

# === USAGE ===
swagger_file = './tests/byanati_new.yaml'      # Input Swagger/OpenAPI file
allowed_txt_file = './tests/allowed_endpoints2.txt' # File with allowed endpoints
output_file = './tests/filtered_swagger2.yaml'      # Output filtered Swagger

# Load data
allowed_endpoints = load_allowed_endpoints(allowed_txt_file)
swagger_data = load_swagger(swagger_file)

# Filter and save
filtered_data = filter_swagger_with_schemas(swagger_data, allowed_endpoints)
save_swagger(filtered_data, output_file)

print(f"Filtered Swagger saved to {output_file} with {len(filtered_data['paths'])} endpoints.")