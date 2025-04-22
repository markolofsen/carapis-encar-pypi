import requests
import yaml
import os
from typing import Optional, Dict, Any, List

# Import configuration
from .config import BASE_URL

# Determine the directory where this script is located
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_PATH = os.path.join(_SCRIPT_DIR, 'schema.yaml')


class CarapisClientError(Exception):
    """Custom exception for CarapisClient errors."""
    pass


class CarapisClient:
    """
    Python client for the Carapis Encar v2 API.
    Loads API definitions from schema.yaml.
    Uses BASE_URL defined in config.py.
    """

    def __init__(self, api_key: str):
        """Initialize the client.

        Args:
            api_key: Your Carapis API key.
        """
        if not api_key:
            raise ValueError("api_key cannot be empty.")

        # Use BASE_URL from config, ensure no trailing slash
        self.base_url = BASE_URL.rstrip('/')
        self.api_key = api_key
        # Define the specific API path part we are interested in
        self.api_base_path = "/apix/encar/v2"
        self._headers = {
            "Accept": "application/json",
            "Authorization": f"ApiKey {self.api_key}",
            "User-Agent": f"CarapisClientPython/{self._get_version()}"  # Include version
        }

        try:
            with open(_SCHEMA_PATH, 'r', encoding='utf-8') as f:
                self._schema = yaml.safe_load(f)
            if not isinstance(self._schema, dict) or 'paths' not in self._schema:
                raise CarapisClientError(f"Invalid schema format in {_SCHEMA_PATH}")
        except FileNotFoundError:
            raise CarapisClientError(f"Schema file not found at {_SCHEMA_PATH}")
        except yaml.YAMLError as e:
            raise CarapisClientError(f"Error parsing schema file {_SCHEMA_PATH}: {e}") from e
        except Exception as e:
            raise CarapisClientError(f"An unexpected error occurred loading schema: {e}") from e

        # Extract only endpoints matching the specified api_base_path
        self._endpoints = self._extract_endpoints(self.api_base_path)

    @staticmethod
    def _get_version() -> str:
        """Reads the version from __init__.py"""
        try:
            init_path = os.path.join(_SCRIPT_DIR, '__init__.py')
            with open(init_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('__version__'):
                        # Execute the line in a temporary dict to get the value
                        local_dict = {}
                        exec(line, globals(), local_dict)
                        return local_dict.get('__version__', 'unknown')
        except Exception:
            pass  # Ignore errors reading version
        return 'unknown'

    def _extract_endpoints(self, base_path_prefix: str) -> Dict[str, Dict[str, Any]]:
        """Extracts endpoints starting with the specified base path from the schema."""
        endpoints = {}
        paths = self._schema.get('paths', {})
        for path, path_item in paths.items():
            # Ensure we only process paths under the specific API base path
            if path.startswith(base_path_prefix):
                # Store the path relative to the api_base_path
                relative_path = path[len(base_path_prefix):]
                if not relative_path.startswith('/'):  # Ensure leading slash
                    relative_path = '/' + relative_path

                for method, operation in path_item.items():
                    # Process only valid HTTP methods
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                        if 'operationId' in operation:
                            op_id = operation['operationId']
                            # Map operationId to method, path, and parameters definition
                            endpoints[op_id] = {
                                'method': method.upper(),
                                'path_template': relative_path,
                                'parameters': operation.get('parameters', [])
                            }
                        else:
                            # Warn if an operation within the target path is missing an ID
                            print(f"Warning: Missing operationId for {method.upper()} {path}")
        return endpoints

    def _request(self, method: str, endpoint_path_template: str,
                 path_params: Optional[Dict[str, Any]] = None,
                 query_params: Optional[Dict[str, Any]] = None,
                 json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper method to make authenticated requests."""
        # Substitute path parameters
        formatted_path = endpoint_path_template
        if path_params:
            try:
                # Ensure all necessary path params are present before formatting
                required_path_vars = [p.strip('{}') for p in endpoint_path_template.split('/') if p.startswith('{')]
                missing_vars = [var for var in required_path_vars if var not in path_params]
                if missing_vars:
                    raise CarapisClientError(f"Missing required path parameters {missing_vars} for endpoint {endpoint_path_template}")
                formatted_path = endpoint_path_template.format(**path_params)
            except KeyError as e:
                # This catch might be redundant now due to the check above, but keep for safety
                raise CarapisClientError(f"Missing path parameter key {e} during formatting for endpoint {endpoint_path_template}") from e

        # Construct the full URL using the class's api_base_path
        url = f"{self.base_url}{self.api_base_path}{formatted_path}"

        # Filter out None values from query_params before sending
        actual_query_params = {k: v for k, v in query_params.items() if v is not None} if query_params else None

        try:
            response = requests.request(
                method,
                url,
                headers=self._headers,
                params=actual_query_params,
                json=json_data,
                timeout=30
            )
            response.raise_for_status()
            # Handle cases where response might be empty (e.g., 204 No Content)
            if response.status_code == 204 or not response.content:
                return {}  # Return empty dict for no content
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_details = response.json()
            except requests.exceptions.JSONDecodeError:
                error_details = response.text  # Use raw text if JSON decoding fails
            raise CarapisClientError(f"HTTP error {response.status_code} for {method} {url}: {error_details}") from e
        except requests.exceptions.RequestException as e:
            raise CarapisClientError(f"Request failed for {method} {url}: {e}") from e
        except ValueError as e:  # Catches JSONDecodeError if response.json() fails above
            raise CarapisClientError(f"Failed to decode JSON response for {method} {url}: {e}") from e

    def _prepare_params(self, operation_id: str, func_args: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Separates function arguments into path and query parameters based on schema."""
        if operation_id not in self._endpoints:
            raise CarapisClientError(f"Unknown operationId: {operation_id}")

        endpoint_info = self._endpoints[operation_id]
        param_defs = endpoint_info.get('parameters', [])

        path_params = {}
        query_params = {}
        known_param_names = set()

        for param_def in param_defs:
            param_name = param_def['name']
            param_in = param_def['in']
            is_required = param_def.get('required', False)
            known_param_names.add(param_name)

            if param_name in func_args:
                value = func_args[param_name]
                # Add to appropriate dictionary if value is not None
                # For required params, _call_endpoint will handle missing value check later if needed
                if value is not None:
                    if param_in == 'path':
                        path_params[param_name] = value
                    elif param_in == 'query':
                        query_params[param_name] = value
                    # Ignore other 'in' types like 'header' or 'cookie' for now
            elif is_required:
                # Raise error immediately if a required parameter is missing (and wasn't passed as None)
                raise CarapisClientError(f"Missing required parameter '{param_name}' for operation '{operation_id}'")

        # Warn about any extra arguments passed that are not in the schema definition
        extra_args = set(func_args.keys()) - known_param_names
        if extra_args:
            print(f"Warning: Unexpected arguments provided for '{operation_id}': {extra_args}")

        return path_params, query_params

    def _call_endpoint(self, operation_id: str, **kwargs) -> Dict[str, Any]:
        """Internal method to prepare and make the API call."""
        if operation_id not in self._endpoints:
            raise CarapisClientError(f"Unknown operationId: {operation_id}")

        endpoint_info = self._endpoints[operation_id]
        method = endpoint_info['method']
        path_template = endpoint_info['path_template']

        # Prepare path and query parameters from kwargs based on schema
        path_params, query_params = self._prepare_params(operation_id, kwargs)

        # Make the request
        # Pass path_params and query_params directly
        return self._request(method, path_template, path_params=path_params, query_params=query_params)

    # --- Explicit Endpoint Methods --- >
    # Signatures are now based on parameters defined in schema.yaml

    def list_dealers(self,
                     limit: Optional[int] = None,
                     ordering: Optional[str] = None,
                     page: Optional[int] = None,
                     search: Optional[str] = None,
                     type: Optional[str] = None) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_business_dealers_list """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_business_dealers_list', **params)

    def get_dealer(self, user_id: str) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_business_dealers_retrieve """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_business_dealers_retrieve', **params)

    def list_diagnosis_centers(self, dealer: Optional[str] = None,
                               limit: Optional[int] = None,
                               ordering: Optional[str] = None,
                               page: Optional[int] = None,
                               search: Optional[str] = None) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_business_diagnosis_centers_list """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_business_diagnosis_centers_list', **params)

    def get_diagnosis_center(self, code: str) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_business_diagnosis_centers_retrieve """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_business_diagnosis_centers_retrieve', **params)

    def list_manufacturers(self, country: Optional[str] = None,
                           limit: Optional[int] = None,
                           ordering: Optional[str] = None,
                           page: Optional[int] = None,
                           search: Optional[str] = None) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_manufacturers_list """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_manufacturers_list', **params)

    def get_manufacturer(self, code: str) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_manufacturers_retrieve """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_manufacturers_retrieve', **params)

    def get_manufacturer_stats(self) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_manufacturers_stats_retrieve """
        # No parameters defined in schema for this operation
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_manufacturers_stats_retrieve', **params)

    def list_model_groups(self, limit: Optional[int] = None,
                          manufacturer: Optional[str] = None,
                          ordering: Optional[str] = None,
                          page: Optional[int] = None,
                          search: Optional[str] = None) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_model_groups_list """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_model_groups_list', **params)

    def get_model_group(self, code: str) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_model_groups_retrieve """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_model_groups_retrieve', **params)

    def list_models(self, limit: Optional[int] = None,
                    model_group: Optional[str] = None,
                    ordering: Optional[str] = None,
                    page: Optional[int] = None,
                    search: Optional[str] = None) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_models_list """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_models_list', **params)

    def get_model(self, code: str) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_catalog_models_retrieve """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_catalog_models_retrieve', **params)

    def list_vehicles(self, body_type: Optional[str] = None, color: Optional[str] = None,
                      fuel_type: Optional[str] = None, grade: Optional[str] = None,
                      has_accidents: Optional[bool] = None, has_repairs: Optional[bool] = None,
                      limit: Optional[int] = None, manufacturer: Optional[str] = None,
                      max_mileage: Optional[int] = None, max_price: Optional[int] = None,
                      max_year: Optional[int] = None, min_mileage: Optional[int] = None,
                      min_price: Optional[int] = None, min_year: Optional[int] = None,
                      model: Optional[str] = None,
                      model_group: Optional[str] = None,
                      ordering: Optional[str] = None,
                      page: Optional[int] = None, search: Optional[str] = None,
                      transmission: Optional[str] = None, vehicle_id: Optional[int] = None,
                      vehicle_no: Optional[str] = None, vin: Optional[str] = None,
                      warranty_type: Optional[str] = None) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_vehicles_list """
        # Collect all parameters passed to the function
        params = locals()
        params.pop('self')  # Remove 'self' from parameters

        # Prepare arguments for _call_endpoint, potentially renaming model_group
        call_kwargs = {}
        for key, value in params.items():
            if key == 'model_group' and value is not None:
                # Map the function argument 'model_group' to the query parameter 'model__model_group'
                call_kwargs['model__model_group'] = value
            elif value is not None:
                # Pass other non-None parameters as is
                call_kwargs[key] = value

        # Important: Pass the modified kwargs to _call_endpoint
        return self._call_endpoint('encar_v2_vehicles_list', **call_kwargs)

    def get_vehicle(self, vehicle_id: int) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_vehicles_retrieve """
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_vehicles_retrieve', **params)

    def get_vehicle_enums(self) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_vehicles_enums_retrieve """
        # No parameters defined in schema
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_vehicles_enums_retrieve', **params)

    def get_vehicle_stats(self) -> Dict[str, Any]:
        """ Corresponds to operationId: encar_v2_vehicles_stats_retrieve """
        # No parameters defined in schema
        params = locals()
        params.pop('self')
        # No kwargs to handle
        return self._call_endpoint('encar_v2_vehicles_stats_retrieve', **params)

    # --- Helper Methods --- >

    def get_endpoint_details(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """ Returns the schema details for a given operationId. """
        return self._endpoints.get(operation_id)

    def list_available_operations(self) -> List[str]:
        """ Lists all available operationIds loaded from the schema. """
        return list(self._endpoints.keys())
