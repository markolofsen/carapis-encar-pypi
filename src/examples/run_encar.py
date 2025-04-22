import os
import sys
import json
import shutil
import logging
from dotenv import load_dotenv
from typing import Optional, Any, Dict, Tuple
from pathlib import Path
from encar import CarapisClient, CarapisClientError

# --- Setup Path --- >
THIS_DIR = Path(__file__).parent
DOWNLOADS_DIR = THIS_DIR / "downloads"
PROJECT_ROOT = THIS_DIR.parent.parent.parent

load_dotenv(
    PROJECT_ROOT / ".env"
)


class EncarApiRunner:
    """Runs a sequence of Carapis API calls, logging results and saving outputs."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.downloads_dir = DOWNLOADS_DIR
        self.logger = self._setup_logging()
        self.client = self._initialize_client()
        self._cleanup_downloads()

    def _setup_logging(self) -> logging.Logger:
        """Configures and returns a logger instance."""
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

        # File Handler (optional, uncomment to enable file logging)
        # log_file = os.path.join(self.script_dir, 'run_encar.log')
        # file_handler = logging.FileHandler(log_file, encoding='utf-8')
        # file_handler.setFormatter(log_formatter)
        # logger.addHandler(file_handler)

        return logger

    def _initialize_client(self) -> CarapisClient:
        """Initializes and returns the CarapisClient."""

        if not self.api_key:
            self.logger.error("CARAPIS_API_KEY is not set.")
            sys.exit(1)
        try:
            client = CarapisClient(api_key=self.api_key)
            self.logger.info(f"CarapisClient initialized for base URL: {client.base_url}")
            return client
        except CarapisClientError as e:
            self.logger.fatal(f"Failed to initialize CarapisClient: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.fatal(f"Unexpected error during client initialization: {e}")
            sys.exit(1)

    def _cleanup_downloads(self):
        """Removes and recreates the downloads directory."""
        self.logger.info(f"Cleaning up downloads directory: {self.downloads_dir}")
        try:
            if os.path.exists(self.downloads_dir):
                shutil.rmtree(self.downloads_dir)
                self.logger.info("Removed existing downloads directory.")
            os.makedirs(self.downloads_dir, exist_ok=True)
            self.logger.info(f"Recreated downloads directory: {self.downloads_dir}")
        except OSError as e:
            self.logger.error(f"Could not clean/create downloads directory {self.downloads_dir}: {e}")
            sys.exit(1)

    def _save_result(self, method_name: str, args: Dict, result: Any):
        """Saves the successful API result to a JSON file."""
        if not isinstance(result, dict) or not result:
            self.logger.debug(f"Skipping save for {method_name}: No valid dictionary result.")
            return

        try:
            filename_parts = [method_name]
            for key_arg in ['vehicle_id', 'code', 'user_id']:
                if key_arg in args and args[key_arg]:
                    filename_parts.append(str(args[key_arg]))

            filename = "_".join(filename_parts) + ".json"
            filepath = os.path.join(self.downloads_dir, filename)

            self.logger.info(f"Saving result of '{method_name}' to: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save result for {method_name} to file: {e}")

    def _run_business_endpoints(self) -> Tuple[Optional[str], Optional[str]]:
        """Runs API calls related to dealers and diagnosis centers."""
        self.logger.info("--- Running Business Endpoints ---")
        fetched_dealer_id = None
        fetched_diag_center_code = None
        res = None  # Initialize res

        # List Dealers
        method_name = "list_dealers"
        limit_arg, ordering_arg = 2, "name"
        args_dict = {"limit": limit_arg, "ordering": ordering_arg}  # For saving
        self.logger.info(f"Calling: {method_name} with limit={limit_arg}, ordering='{ordering_arg}'")
        try:
            # Explicit arguments
            res = self.client.list_dealers(limit=limit_arg, ordering=ordering_arg)
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res)
            if res and res.get('results') and len(res['results']) > 0:
                fetched_dealer_id = res['results'][0].get('user_id')
                self.logger.info(f"---> Fetched dealer_id: {fetched_dealer_id}")
            else:
                self.logger.warning("---> Could not fetch dealer_id from list_dealers.")
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

        # Get Dealer (if ID fetched)
        if fetched_dealer_id:
            method_name = "get_dealer"
            args_dict = {"user_id": fetched_dealer_id}  # For saving
            self.logger.info(f"Calling: {method_name} with user_id='{fetched_dealer_id}'")
            try:
                # Explicit argument
                res_dealer = self.client.get_dealer(user_id=fetched_dealer_id)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_dealer)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        else:
            self.logger.warning("Skipping get_dealer - No ID fetched.")

        # List Diagnosis Centers
        method_name = "list_diagnosis_centers"
        limit_arg = 2
        args_dict = {"limit": limit_arg}  # For saving
        self.logger.info(f"Calling: {method_name} with limit={limit_arg}")
        res = None  # Reset res
        try:
            # Explicit argument
            res = self.client.list_diagnosis_centers(limit=limit_arg)
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res)
            if res and res.get('results') and len(res['results']) > 0:
                fetched_diag_center_code = res['results'][0].get('code')
                self.logger.info(f"---> Fetched diagnosis center code: {fetched_diag_center_code}")
            else:
                self.logger.warning("---> Could not fetch diagnosis center code from list_diagnosis_centers.")
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

        # Get Diagnosis Center (if code fetched)
        if fetched_diag_center_code:
            method_name = "get_diagnosis_center"
            args_dict = {"code": fetched_diag_center_code}  # For saving
            self.logger.info(f"Calling: {method_name} with code='{fetched_diag_center_code}'")
            try:
                # Explicit argument
                res_diag = self.client.get_diagnosis_center(code=fetched_diag_center_code)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_diag)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        else:
            self.logger.warning("Skipping get_diagnosis_center - No code fetched.")

        return fetched_dealer_id, fetched_diag_center_code

    def _run_catalog_endpoints(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Runs API calls related to manufacturers, model groups, and models."""
        self.logger.info("--- Running Catalog Endpoints ---")
        fetched_manufacturer_code = None
        fetched_model_group_code = None
        fetched_model_code = None
        res = None  # Initialize res

        # List Manufacturers
        method_name = "list_manufacturers"
        limit_arg = 2
        args_dict = {"limit": limit_arg}  # For saving
        self.logger.info(f"Calling: {method_name} with limit={limit_arg}")
        try:
            # Explicit argument
            res = self.client.list_manufacturers(limit=limit_arg)
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res)
            if res and res.get('results') and len(res['results']) > 0:
                fetched_manufacturer_code = res['results'][0].get('code')
                self.logger.info(f"---> Fetched manufacturer code: {fetched_manufacturer_code}")
            else:
                self.logger.warning("---> Could not fetch manufacturer code from list_manufacturers.")
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

        if fetched_manufacturer_code:
            # Get Manufacturer
            method_name = "get_manufacturer"
            args_dict = {"code": fetched_manufacturer_code}  # For saving
            self.logger.info(f"Calling: {method_name} with code='{fetched_manufacturer_code}'")
            try:
                # Explicit argument
                res_mfr = self.client.get_manufacturer(code=fetched_manufacturer_code)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_mfr)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

            # List Model Groups
            method_name = "list_model_groups"
            limit_arg, ordering_arg = 2, "name"
            args_dict = {"manufacturer": fetched_manufacturer_code, "limit": limit_arg, "ordering": ordering_arg}  # For saving
            res_mg = None
            self.logger.info(f"Calling: {method_name} with manufacturer='{fetched_manufacturer_code}', limit={limit_arg}, ordering='{ordering_arg}'")
            try:
                # Explicit arguments
                res_mg = self.client.list_model_groups(manufacturer=fetched_manufacturer_code, limit=limit_arg, ordering=ordering_arg)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_mg)
                if res_mg and res_mg.get('results') and len(res_mg['results']) > 0:
                    fetched_model_group_code = res_mg['results'][0].get('code')
                    self.logger.info(f"---> Fetched model group code: {fetched_model_group_code}")
                else:
                    self.logger.warning("---> Could not fetch model group code from list_model_groups.")
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        else:
            self.logger.warning("Skipping manufacturer-dependent catalog calls - No manufacturer code fetched.")

        # Get Manufacturer Stats (Known to fail currently)
        method_name = "get_manufacturer_stats"
        args_dict = {}  # For saving
        self.logger.info(f"Calling: {method_name} (no args)")
        try:
            # No arguments
            res_mfr_stats = self.client.get_manufacturer_stats()
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res_mfr_stats)
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

        if fetched_model_group_code:
            # Get Model Group
            method_name = "get_model_group"
            args_dict = {"code": fetched_model_group_code}  # For saving
            self.logger.info(f"Calling: {method_name} with code='{fetched_model_group_code}'")
            try:
                # Explicit argument
                res_get_mg = self.client.get_model_group(code=fetched_model_group_code)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_get_mg)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

            # List Models
            method_name = "list_models"
            limit_arg = 2
            args_dict = {"model_group": fetched_model_group_code, "limit": limit_arg}  # For saving
            res_mdl = None
            self.logger.info(f"Calling: {method_name} with model_group='{fetched_model_group_code}', limit={limit_arg}")
            try:
                # Explicit arguments
                res_mdl = self.client.list_models(model_group=fetched_model_group_code, limit=limit_arg)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_mdl)
                if res_mdl and res_mdl.get('results') and len(res_mdl['results']) > 0:
                    fetched_model_code = res_mdl['results'][0].get('code')
                    self.logger.info(f"---> Fetched model code: {fetched_model_code}")
                else:
                    self.logger.warning("---> Could not fetch model code from list_models.")
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        else:
            self.logger.warning("Skipping model group-dependent catalog calls - No model group code fetched.")

        if fetched_model_code:
            # Get Model
            method_name = "get_model"
            args_dict = {"code": fetched_model_code}  # For saving
            self.logger.info(f"Calling: {method_name} with code='{fetched_model_code}'")
            try:
                # Explicit argument
                res_get_mdl = self.client.get_model(code=fetched_model_code)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_get_mdl)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        else:
            self.logger.warning("Skipping get_model - No model code fetched.")

        return fetched_manufacturer_code, fetched_model_group_code, fetched_model_code

    def _run_vehicle_endpoints(self, fetched_manufacturer_code: Optional[str], fetched_model_group_code: Optional[str]):
        """Runs API calls related to vehicles."""
        self.logger.info("--- Running Vehicle Endpoints ---")
        fetched_vehicle_id = None
        res_list = None  # Initialize

        # List Vehicles (simple, to get an ID)
        method_name = "list_vehicles_for_id"
        limit_arg, ordering_arg = 1, "-created_at"
        args_dict = {"limit": limit_arg, "ordering": ordering_arg}  # For saving
        self.logger.info(f"Calling: {method_name} with limit={limit_arg}, ordering='{ordering_arg}'")
        try:
            # Explicit arguments
            res_list = self.client.list_vehicles(limit=limit_arg, ordering=ordering_arg)
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res_list)
            if res_list and res_list.get('results') and len(res_list['results']) > 0:
                fetched_vehicle_id = res_list['results'][0].get('vehicle_id')
                self.logger.info(f"---> Fetched vehicle_id: {fetched_vehicle_id}")
            else:
                self.logger.warning("---> Could not fetch vehicle_id from list_vehicles.")
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

        # --- Additional List Examples ---
        if fetched_manufacturer_code:
            method_name_base = "list_vehicles_by_manufacturer"
            method_name_save = f"list_vehicles_by_{fetched_manufacturer_code}"  # Filename
            limit_arg = 2
            args_dict = {"limit": limit_arg, "manufacturer": fetched_manufacturer_code}  # For saving
            self.logger.info(f"Calling: {method_name_base} with limit={limit_arg}, manufacturer='{fetched_manufacturer_code}'")
            try:
                # Explicit arguments
                res_mfr_list = self.client.list_vehicles(limit=limit_arg, manufacturer=fetched_manufacturer_code)
                self.logger.info(f"SUCCESS: {method_name_base} for {fetched_manufacturer_code}")
                self._save_result(method_name_save, args_dict, res_mfr_list)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name_base} for {fetched_manufacturer_code} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name_base} for {fetched_manufacturer_code} - {type(e).__name__}: {e}")

        if fetched_manufacturer_code and fetched_model_group_code:
            # NOTE: model_group filter is now handled by the client library
            method_name_base = "list_vehicles_by_manufacturer_model_group"
            method_name_save = f"list_vehicles_{fetched_manufacturer_code}_{fetched_model_group_code}"  # Filename
            limit_arg = 2
            args_dict = {"limit": limit_arg, "manufacturer": fetched_manufacturer_code, "model_group": fetched_model_group_code}  # For saving
            self.logger.info(f"Attempting {method_name_base} with limit={limit_arg}, manufacturer='{fetched_manufacturer_code}', model_group='{fetched_model_group_code}'")
            try:
                # Explicit arguments
                res_mfr_mg_list = self.client.list_vehicles(limit=limit_arg, manufacturer=fetched_manufacturer_code, model_group=fetched_model_group_code)
                self.logger.info(f"SUCCESS: {method_name_base} for {fetched_manufacturer_code}/{fetched_model_group_code}")
                self._save_result(method_name_save, args_dict, res_mfr_mg_list)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name_base} for {fetched_manufacturer_code}/{fetched_model_group_code} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name_base} for {fetched_manufacturer_code}/{fetched_model_group_code} - {type(e).__name__}: {e}")

        method_name = "list_vehicles_year_2022"
        limit_arg, min_year_arg, max_year_arg = 2, 2022, 2022
        args_dict = {"limit": limit_arg, "min_year": min_year_arg, "max_year": max_year_arg}  # For saving
        self.logger.info(f"Calling: {method_name} with limit={limit_arg}, min_year={min_year_arg}, max_year={max_year_arg}")
        try:
            # Explicit arguments
            res_year_list = self.client.list_vehicles(limit=limit_arg, min_year=min_year_arg, max_year=max_year_arg)
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res_year_list)
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        # --- < Additional List Examples ---

        # Get Vehicle (if ID fetched)
        if fetched_vehicle_id:
            method_name = "get_vehicle"
            args_dict = {"vehicle_id": fetched_vehicle_id}  # For saving
            self.logger.info(f"Calling: {method_name} with vehicle_id={fetched_vehicle_id}")
            try:
                # Explicit argument
                res_vehicle = self.client.get_vehicle(vehicle_id=fetched_vehicle_id)
                self.logger.info(f"SUCCESS: {method_name}")
                self._save_result(method_name, args_dict, res_vehicle)
            except CarapisClientError as e:
                self.logger.error(f"FAILED (API Error): {method_name} - {e}")
            except Exception as e:
                self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")
        else:
            self.logger.warning("Skipping get_vehicle - No ID fetched.")

        # Get Vehicle Enums
        method_name = "get_vehicle_enums"
        args_dict = {}  # For saving
        self.logger.info(f"Calling: {method_name} (no args)")
        try:
            # No arguments
            res_enums = self.client.get_vehicle_enums()
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res_enums)
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

        # Get Vehicle Stats
        method_name = "get_vehicle_stats"
        args_dict = {}  # For saving
        self.logger.info(f"Calling: {method_name} (no args)")
        try:
            # No arguments
            res_stats = self.client.get_vehicle_stats()
            self.logger.info(f"SUCCESS: {method_name}")
            self._save_result(method_name, args_dict, res_stats)
        except CarapisClientError as e:
            self.logger.error(f"FAILED (API Error): {method_name} - {e}")
        except Exception as e:
            self.logger.error(f"FAILED (Unexpected Error): {method_name} - {type(e).__name__}: {e}")

    def run(self):
        """Executes the full sequence of API calls."""
        self.logger.info("=== Starting Encar API Run ===")
        _, _ = self._run_business_endpoints()
        mfr_code, mg_code, _ = self._run_catalog_endpoints()
        self._run_vehicle_endpoints(mfr_code, mg_code)
        self.logger.info("=== Finished Encar API Run ===")


def main():
    api_key = os.environ.get("CARAPIS_API_KEY")  # Removed default key

    if not api_key:
        # Logger is not initialized yet, use print for this critical error
        print("CRITICAL: CARAPIS_API_KEY environment variable not set.")
        print("Alternatively, export the environment variable.")
        sys.exit(1)

    try:
        runner = EncarApiRunner(api_key)
        runner.run()
    except Exception as e:
        # Catch any unexpected error during runner instantiation or run
        # Use print as logger might not be fully set up if error is early
        print(f"\nUNEXPECTED CRITICAL ERROR: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
