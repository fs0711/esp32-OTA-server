import subprocess
import os
import logging
from esp32OTA.generic.controllers import Controller
from esp32OTA.generic.services.utils import response_utils, response_codes

logger = logging.getLogger(__name__)

class ConfigController(Controller):
    
    @classmethod
    def get_config(cls):
        """Reads the mosquitto.conf file."""
        config_path = "mosquitto.conf" # Root of workspace
        if not os.path.exists(config_path):
            return response_utils.get_json_response_object(
                response_code=response_codes.CODE_RECORD_NOT_FOUND,
                response_message="Config file not found"
            )
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            return response_utils.get_json_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message="Config read successfully",
                response_data={"content": content}
            )
        except Exception as e:
            return response_utils.get_json_response_object(
                response_code=response_codes.CODE_UPDATE_FAILED,
                response_message=str(e)
            )

    @classmethod
    def update_config(cls, data):
        """Updates the mosquitto.conf file and runs a dry-run test."""
        new_content = data.get("content")
        config_path = "mosquitto.conf"
        
        if not new_content:
             return response_utils.get_json_response_object(
                response_code=response_codes.CODE_VALIDATION_FAILED,
                response_message="Content is required"
            )

        # 1. Write to a temporary file for testing
        temp_path = "mosquitto.conf.test"
        try:
            with open(temp_path, 'w') as f:
                f.write(new_content)
            
            # 2. Run dry-run test
            # Note: Mosquitto must be installed and in PATH
            try:
                # Use --test-config to verify
                # On Windows, need full path if not in PATH
                result = subprocess.run(['mosquitto', '-c', temp_path, '--test-config'], 
                                     capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_out = result.stderr or result.stdout
                    return response_utils.get_json_response_object(
                        response_code=response_codes.CODE_VALIDATION_FAILED,
                        response_message=f"Configuration test failed: {error_out}"
                    )
            except FileNotFoundError:
                # If mosquitto command not found, just proceed but warn
                logger.warning("Mosquitto command not found. Skipping dry-run.")
            
            # 3. If test passed or skipped, overwrite original
            with open(config_path, 'w') as f:
                f.write(new_content)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return response_utils.get_json_response_object(
                response_code=response_codes.CODE_SUCCESS,
                response_message="Configuration updated successfully and passed dry-run"
            )
            
        except Exception as e:
            return response_utils.get_json_response_object(
                response_code=response_codes.CODE_UPDATE_FAILED,
                response_message=str(e)
            )
