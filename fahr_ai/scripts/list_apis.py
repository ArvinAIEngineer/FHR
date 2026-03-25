import yaml
import json

def load_swagger(file_path):
    with open(file_path, 'r') as f:
        if file_path.endswith(('.yaml', '.yml')):
            return yaml.safe_load(f)
        elif file_path.endswith('.json'):
            return json.load(f)
        else:
            raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")

def list_endpoints_with_summary(swagger_dict):
    paths = swagger_dict.get('paths', {})
    filtered_endpoints = []

    for path, methods in paths.items():
        if any(
            isinstance(operation, dict) and 'summary' in operation
            for operation in methods.values()
        ):
            filtered_endpoints.append(path)

    return filtered_endpoints

def save_to_file(endpoints, output_file):
    with open(output_file, 'w') as f:
        for ep in endpoints:
            f.write(ep + '\n')

# === Usage ===
swagger_file = './tests/filtered_swagger2.yaml'     # or 'swagger.json'
output_file = './tests/endpoints.txt'

swagger_data = load_swagger(swagger_file)
endpoints = list_endpoints_with_summary(swagger_data)
save_to_file(endpoints, output_file)

print(f"Saved {len(endpoints)} endpoints (with summaries) to {output_file}")
