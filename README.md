# Encar – Official Python Client for Encar API

[![PyPI version](https://badge.fury.io/py/encar.svg)](https://pypi.org/project/encar/)
[![API Docs](https://img.shields.io/badge/API%20Docs-Carapis%20Encar%20API-blue)](https://carapis.com/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Carapis Catalog](https://img.shields.io/badge/Live%20Catalog-Carapis.com-green)](https://carapis.com/catalog)

**Encar** is the official Python client for the **Carapis Encar API**, providing seamless programmatic access to real-time Korean used car data from Encar.com. With the `encar` library, you can easily query, filter, and analyze vehicle listings, manufacturers, models, and more – all powered by the robust **Encar API** provided by Carapis.com.

Explore a live catalog powered by this **Encar API**: [Carapis Catalog](https://carapis.com/catalog)

## Features

- Easy access to real-time Encar.com vehicle data via **Carapis Encar API**
- List, filter, and retrieve detailed car listings using the **Encar API**
- Fetch manufacturer, model, and vehicle details programmatically
- Supports advanced search queries for the **Encar API**
- Free tier available for testing the **Encar API** (up to 1,000 vehicles)

## Installation

Install the `encar` library using pip. Dependencies are handled automatically.

```bash
pip install encar
```

## Configuration

1.  **API Key**: The client requires a **Carapis Encar API** key for full access. Get yours at [Carapis.com Pricing](https://carapis.com/pricing). Retrieve this key from a secure location, such as environment variables.

    *Without an API key, **Encar API** access is limited to the latest 1,000 vehicles (Free Tier).*

## How to use Encar API (Python Client)

Initialize the client and make **Encar API** calls.

```python
import os
from encar import CarapisClient, CarapisClientError

# Retrieve the Encar API key from environment variables
API_KEY = os.getenv("CARAPIS_API_KEY")

if not API_KEY:
    print("Error: CARAPIS_API_KEY environment variable not set. Exiting.")
    # Full Encar API access requires a valid key.
    exit()

try:
    # Initialize Encar API client
    client = CarapisClient(api_key=API_KEY)
    print("Carapis Encar API Client initialized successfully.")

    # --- Proceed with Encar API calls below ---

except CarapisClientError as e:
    print(f"Encar API Client Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

---

## Encar API Python Usage Examples

Below are examples for querying the **Encar API** using this client.

### List Vehicles via Encar API

Retrieve a list of vehicles with filtering.

```python
try:
    print("\n--- Querying Encar API for Vehicles ---")
    # Fetch vehicle data via Encar API
    vehicles = client.list_vehicles(
        limit=5,
        min_year=2021,
        fuel_type='gasoline',
        max_mileage=50000,
        ordering='-created_at'
    )
    print("Vehicles Found via Encar API:")
    if vehicles and vehicles.get('results'):
        for v in vehicles['results']:
             print(f"- ID: {v.get('vehicle_id')}, Model: {v.get('model_name', 'N/A')}, Price: {v.get('price')}")
    else:
        print("No vehicles found.")

except CarapisClientError as e:
    print(f"Encar API Error listing vehicles: {e}")
```

### Get Vehicle Details via Encar API

Retrieve details for a specific vehicle.

```python
try:
    vehicle_id_to_get = 12345678 # Replace with a valid ID
    print(f"\n--- Getting Vehicle Details from Encar API (ID: {vehicle_id_to_get}) ---")
    # Fetch specific vehicle details via Encar API
    vehicle_details = client.get_vehicle(vehicle_id=vehicle_id_to_get)
    print("Vehicle Details Received from Encar API:")
    print(vehicle_details)

except CarapisClientError as e:
    print(f"Encar API Error getting vehicle {vehicle_id_to_get}: {e}")
```

### List Manufacturers via Encar API

Retrieve a list of vehicle manufacturers.

```python
try:
    print("\n--- Listing Manufacturers from Encar API ---")
    # Fetch manufacturers via Encar API
    manufacturers = client.list_manufacturers(country='KR', limit=10)
    print("Manufacturers Found via Encar API:")
    if manufacturers and manufacturers.get('results'):
        for mfr in manufacturers['results']:
             print(f"- Code: {mfr.get('code')}, Name: {mfr.get('name')}")
    else:
        print("No manufacturers found.")

except CarapisClientError as e:
    print(f"Encar API Error listing manufacturers: {e}")
```

### Get Manufacturer Details via Encar API

Retrieve details for a specific manufacturer by its code.

```python
try:
    manufacturer_code = '101' # Example: Hyundai
    print(f"\n--- Getting Manufacturer Details from Encar API (Code: {manufacturer_code}) ---")
    manufacturer_info = client.get_manufacturer(code=manufacturer_code)
    print("Manufacturer Details Received from Encar API:")
    print(manufacturer_info)

except CarapisClientError as e:
    print(f"Encar API Error getting manufacturer {manufacturer_code}: {e}")
```

### Get Manufacturer Stats via Encar API

Retrieve overall statistics about manufacturers.

```python
try:
    print("\n--- Getting Manufacturer Stats from Encar API ---")
    mfr_stats = client.get_manufacturer_stats()
    print("Manufacturer Statistics Received from Encar API:")
    print(mfr_stats)

except CarapisClientError as e:
    print(f"Encar API Error getting manufacturer stats: {e}")
```

### List Model Groups via Encar API

Retrieve a list of model groups, optionally filtered.

```python
try:
    manufacturer_code = '101' # Example: Hyundai
    print(f"\n--- Listing Model Groups from Encar API (Manufacturer: {manufacturer_code}) ---")
    # Fetch model groups via Encar API
    model_groups = client.list_model_groups(manufacturer=manufacturer_code, search='Avante', limit=5)
    print("Model Groups Found via Encar API:")
    if model_groups and model_groups.get('results'):
        for mg in model_groups['results']:
             print(f"- Code: {mg.get('code')}, Name: {mg.get('name')}")
    else:
        print("No model groups found.")

except CarapisClientError as e:
    print(f"Encar API Error listing model groups: {e}")
```

### Get Model Group Details via Encar API

Retrieve details for a specific model group by its code.

```python
try:
    model_group_code = '1101' # Example: Avante
    print(f"\n--- Getting Model Group Details from Encar API (Code: {model_group_code}) ---")
    # Fetch model group details via Encar API
    model_group_info = client.get_model_group(code=model_group_code)
    print("Model Group Details Received from Encar API:")
    print(model_group_info)

except CarapisClientError as e:
    print(f"Encar API Error getting model group {model_group_code}: {e}")
```

### List Models via Encar API

Retrieve a list of specific vehicle models, optionally filtered.

```python
try:
    model_group_code = '1101' # Example: Avante
    print(f"\n--- Listing Models from Encar API (Model Group: {model_group_code}) ---")
    # Fetch models via Encar API
    models = client.list_models(model_group=model_group_code, search='CN7', limit=5)
    print("Models Found via Encar API:")
    if models and models.get('results'):
        for mdl in models['results']:
             print(f"- Code: {mdl.get('code')}, Name: {mdl.get('name')}")
    else:
        print("No models found.")

except CarapisClientError as e:
    print(f"Encar API Error listing models: {e}")
```

### Get Model Details via Encar API

Retrieve details for a specific vehicle model by its code.

```python
try:
    model_code = '21101' # Example: Specific Avante model
    print(f"\n--- Getting Model Details from Encar API (Code: {model_code}) ---")
    # Fetch model details via Encar API
    model_info = client.get_model(code=model_code)
    print("Model Details Received from Encar API:")
    print(model_info)

except CarapisClientError as e:
    print(f"Encar API Error getting model {model_code}: {e}")
```

### List Dealers via Encar API

Retrieve a list of dealers.

```python
try:
    print("\n--- Listing Dealers from Encar API ---")
    # Fetch dealers via Encar API
    dealers = client.list_dealers(limit=5, ordering='name')
    print("Dealers Found via Encar API:")
    if dealers and dealers.get('results'):
        for dealer in dealers['results']:
            print(f"- User ID: {dealer.get('user_id')}, Name: {dealer.get('name')}, Type: {dealer.get('type')}")
    else:
        print("No dealers found.")

except CarapisClientError as e:
    print(f"Encar API Error listing dealers: {e}")
```

### Get Dealer Details via Encar API

Retrieve details for a specific dealer by User ID.

```python
try:
    dealer_user_id = 'some_dealer_id' # Replace with a valid User ID
    print(f"\n--- Getting Dealer Details from Encar API (User ID: {dealer_user_id}) ---")
    # Fetch dealer details via Encar API
    dealer_details = client.get_dealer(user_id=dealer_user_id)
    print("Dealer Details Received from Encar API:")
    print(dealer_details)

except CarapisClientError as e:
    print(f"Encar API Error getting dealer {dealer_user_id}: {e}")
```

### List Diagnosis Centers via Encar API

Retrieve a list of diagnosis centers.

```python
try:
    dealer_user_id = 'some_dealer_id' # Optionally filter by dealer ID
    print(f"\n--- Listing Diagnosis Centers from Encar API (Dealer: {dealer_user_id or 'Any'}) ---")
    # Fetch diagnosis centers via Encar API
    centers = client.list_diagnosis_centers(dealer=dealer_user_id, limit=5)
    print("Diagnosis Centers Found via Encar API:")
    if centers and centers.get('results'):
        for center in centers['results']:
            print(f"- Code: {center.get('code')}, Name: {center.get('name')}, Dealer: {center.get('dealer')}")
    else:
        print("No diagnosis centers found.")

except CarapisClientError as e:
    print(f"Encar API Error listing diagnosis centers: {e}")
```

### Get Diagnosis Center Details via Encar API

Retrieve details for a specific diagnosis center by its code.

```python
try:
    center_code = 'DC001' # Replace with a valid Center Code
    print(f"\n--- Getting Diagnosis Center Details from Encar API (Code: {center_code}) ---")
    # Fetch center details via Encar API
    center_details = client.get_diagnosis_center(code=center_code)
    print("Diagnosis Center Details Received from Encar API:")
    print(center_details)

except CarapisClientError as e:
    print(f"Encar API Error getting diagnosis center {center_code}: {e}")
```

### Get Vehicle Enums via Encar API

Retrieve possible enum values used in vehicle data (e.g., for `FuelType`, `Color`).

```python
try:
    print("\n--- Getting Vehicle Enums from Encar API ---")
    # Fetch enums via Encar API
    enums = client.get_vehicle_enums()
    print("Available Enums Received from Encar API:")
    if enums:
        print(f"- Fuel Types: {list(enums.get('FuelType', {}).keys())}")
        print(f"- Colors: {list(enums.get('Color', {}).keys())}")
        # Add more as needed
    else:
         print("Could not retrieve enums.")

except CarapisClientError as e:
    print(f"Encar API Error getting enums: {e}")
```

### Get Vehicle Stats via Encar API

Retrieve overall statistics about vehicles in the database.

```python
try:
    print("\n--- Getting Vehicle Stats from Encar API ---")
    # Fetch stats via Encar API
    vehicle_stats = client.get_vehicle_stats()
    print("Vehicle Statistics Received from Encar API:")
    print(vehicle_stats)

except CarapisClientError as e:
    print(f"Encar API Error getting stats: {e}")
```

*(Refer to the [Encar API documentation](https://carapis.com/docs) for full details on all methods and parameters.)*

---

## Direct Encar API Access & Documentation

Interact with the **Encar API** directly using `curl` or other HTTP clients.

**Full Encar API Documentation:** [https://carapis.com/docs](https://carapis.com/docs)

**Example `curl` Requests for Encar API:**

*   **With API Key (Full Encar API Access):**
    ```bash
    # Query Encar API for vehicles
    curl -X 'GET' \
      'https://carapis.com/apix/encar/v2/vehicles/?limit=5&min_year=2021' \
      -H 'accept: application/json' \
      -H 'Authorization: ApiKey YOUR_API_KEY_UUID'
    ```

*   **Without API Key (Free Tier Encar API Access - 1,000 Record Limit):**
    ```bash
    # Limited query to Encar API
    curl -X 'GET' \
      'https://carapis.com/apix/encar/v2/vehicles/?limit=5' \
      -H 'accept: application/json'
    ```

See [Carapis Pricing Plans](https://carapis.com/pricing) for **Encar API** access tiers.

## See Also

- [Carapis.com](https://carapis.com) - The provider of this Encar API.
- [Encar.com](https://encar.com) - The primary source of the vehicle data.

## Support & Contact

- Website: [https://carapis.com](https://carapis.com)
- Telegram: [t.me/markinmatrix](https://t.me/markinmatrix)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
