import base64
import io
import shutil
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from PIL import Image
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
from datetime import datetime, timedelta
from .models import AppUser,DynamicExcelData
import pandas as pd
from django.db import connection # Import the AppUser model
import xlrd  # For reading .xls files
import xlwt
from selenium.webdriver.common.action_chains import ActionChains
import platform
from django.views.decorators.http import require_POST

def fetch_site_username(app_username):
    try:
        # Fetch the user's website username (site_username) from the database
        user = AppUser.objects.get(app_username=app_username)
        site_username = user.site_username  # Store the site_username in a variable
        return site_username

    except AppUser.DoesNotExist:
        print(f"No user found with app_username: {app_username}")
        return None

def fetch_site_password(app_username):
    try:
        # Fetch the user's website password (site_password) from the database
        user = AppUser.objects.get(app_username=app_username)
        site_password = user.site_password  # Store the site_password in a variable
        return site_password

    except AppUser.DoesNotExist:
        print(f"No user found with app_username: {app_username}")
        return None



def  initialize_driver():
    download_dir = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
    if platform.system() == "Windows":
        print(platform.system())
        driver_path = os.path.join(base_dir, 'drivers', 'chromedriver.exe')  # Set your Windows ChromeDriver path here
    elif platform.system() == "Linux":
        print(platform.system())
        driver_path = os.path.join(base_dir, 'drivers', 'chromedriver')  # Set your Linux ChromeDriver path here
    else:
        raise Exception("Unsupported OS. This script only supports Windows and Linux.")
    # driver_path = os.path.join(base_dir, 'drivers', 'chromedriver.exe')
    service = Service(driver_path)

    # Specify the directory where you want to save the downloaded Excel files
      # Update this path

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Set the download directory
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option("prefs", prefs)
    #
    # Add headless mode if desired
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://tmsreports.pmjay.gov.in/OneTMS/loginnew.htm")
    return driver

def login_site(driver,site_username, site_password):
    username_field = driver.find_element(By.NAME, 'username')
    username_field.clear()
    username_field.send_keys(site_username)
    process = driver.find_element(By.ID, 'proceed')
    process.click()
    time.sleep(10)
    try:
        close_button = driver.find_element(By.CLASS_NAME, 'bootbox-close-button')
        close_button.click()
    except Exception:
        pass
    password_field = driver.find_element(By.NAME, 'password')
    password_field.clear()
    password_field.send_keys(site_password)
    try:
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.bootbox-accept"))
        )
        button.click()
    except Exception:
        pass
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close"))
        )
        close_button.click()
        login_site(driver, site_username, site_password)
    except Exception:
        pass

    captcha_download(driver)


def captcha_download(driver):
    # Directory where captcha images will be saved
    captcha_directory = "L_and_R/media/captchas"

    # Ensure the directory exists
    if not os.path.exists(captcha_directory):
        os.makedirs(captcha_directory)

    # Delete any existing files in the captcha directory
    for filename in os.listdir(captcha_directory):
        file_path = os.path.join(captcha_directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    # Locate the captcha image element
    captcha_element = driver.find_element(By.NAME, 'captchaImg')
    captcha_src = captcha_element.get_attribute('src')

    # Extract and save the captcha image
    if "data:image/jpeg;base64," in captcha_src:
        captcha_base64 = captcha_src.split(",")[1]
        captcha_image_data = base64.b64decode(captcha_base64)
        captcha_image = Image.open(io.BytesIO(captcha_image_data))

        # Save the image with a temporary name to avoid conflicts
        captcha_image_path = os.path.join(captcha_directory, "captcha_image.jpg")

        try:
            captcha_image.save(captcha_image_path)
        except Exception as e:
            print(f'Failed to save captcha image. Reason: {e}')
def captcha_solve(driver,captcha):

    # captcha_input = input("Enter captcha: ")
    captcha_element = driver.find_element(By.NAME, 'reqCaptcha')
    captcha_element.send_keys(captcha)
    click_to_login = driver.find_element(By.NAME, 'checkSubmit')
    click_to_login.click()
    login_button = driver.find_element(By.ID, 'login-submit')
    login_button.click()
    time.sleep(10)
    try:
        skip_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'skipBtn'))
        )
        time.sleep(2)  # Add a short delay to ensure the button is fully ready
        skip_button.click()
    except Exception as e:
        pass

    try:
        # Wait for the close button to be present
        close_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn.btn-default[data-dismiss='modal']"))
        )
        print("Close button found.")

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView(true);", close_button)

        # Get button's position
        location = close_button.location
        size = close_button.size

        # Scroll window to the button's coordinates
        driver.execute_script(f"window.scrollTo({location['x']}, {location['y']});")

        # Use ActionChains to click at the button's coordinates
        actions = ActionChains(driver)
        actions.move_by_offset(location['x'] + size['width'] / 2, location['y'] + size['height'] / 2).click().perform()
        print("Clicked the close button using coordinates.")

    except Exception:
        pass

def input_case_type(driver, case_type):
    try:
        # Wait for the skip button to be clickable with a timeout of 10 seconds
        skip_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "skipBtn"))
        )
        skip_button.click()
        print("Skip button clicked successfully!")
    except TimeoutException:
        print("Skip button did not become clickable in time.")
    except Exception as e:
        print(f"Failed to click the skip button. Error: {str(e)}")

    menu_toggle = driver.find_element(By.ID, "menu_toggle")
    menu_toggle.click()
    try:
        # Wait for the element to be clickable
        cases_search = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Cases Search')]"))
        )
        print("Cases Search element found.")

        # Scroll the element into view and click
        driver.execute_script("arguments[0].scrollIntoView(true);", cases_search)
        cases_search.click()
        print("Cases Search element clicked successfully.")

    except TimeoutException:
        print("Cases Search element did not appear within the time limit.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


    try:
        iframe = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "middleFrame"))
        )
        driver.switch_to.frame(iframe)
        # time.sleep(2)
        Casetype = driver.find_element(By.ID, "select2-caseType-container")
        Casetype.click()
        time.sleep(2)
        input_element = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
        input_element.send_keys(case_type, Keys.ENTER)
        dropdown = Select(driver.find_element(By.ID, 'dateType'))
        dropdown.select_by_value('ADS92')
    except (NoSuchElementException, TimeoutException):
        input_case_type(driver,case_type)

def input_scheme(driver,scheme):
    Scheme = driver.find_element(By.ID, "select2-selectedScheme-container")
    Scheme.click()
    time.sleep(2)
    input_element = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
    input_element.send_keys(scheme, Keys.ENTER)

def input_period(driver,record):
    select_element = driver.find_element(By.ID, "recordPeriod")
    select = Select(select_element)
    select.select_by_value(record)


 # Import your model where the data will be stored


def download_excel(driver, scheme, record):
    base_directory = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create a subdirectory with the scheme name if it doesn't exist
    scheme_directory = os.path.join(base_directory, scheme)
    if not os.path.exists(scheme_directory):
        os.makedirs(scheme_directory)

    # Perform the download
    time.sleep(2)
    button = driver.find_element(By.CSS_SELECTOR, ".btn.btn-success")
    button.click()

    try:
        # Check if the second button (image_element) exists
        image_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "excelImg"))
        )
        # If the element is found, click it to download the Excel file
        image_element.click()
        time.sleep(15)  # Wait for the download to complete

        # Find the latest downloaded file
        files = os.listdir(base_directory)
        files = [f for f in files if f.endswith('.xls')]
        if not files:
            raise FileNotFoundError("No Excel files found in the download directory.")

        latest_file = max([os.path.join(base_directory, f) for f in files], key=os.path.getctime)

        # Destination path in the scheme-specific subdirectory
        new_file_name = os.path.join(scheme_directory, f"{scheme}_{record}report{timestamp}.xls")

        # Move the file to the scheme-specific directory and rename it
        shutil.move(latest_file, new_file_name)
        print(f"Excel file for {scheme} downloaded and saved to {new_file_name}")

        # Process the Excel file and upload its contents to the database
        # process_excel_file_and_upload(new_file_name, scheme)

        return "success"  # Return success status

    except TimeoutException:
        print("No records found on the page.")
        return "no_records"  # Return no records status


def download_excel1(driver, scheme, fromdate, todate):
    base_directory = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')

    scheme_directory = os.path.join(base_directory, scheme)
    if not os.path.exists(scheme_directory):
        os.makedirs(scheme_directory)

    wait = WebDriverWait(driver, 5)

    try:
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.bootbox-accept")))
        button.click()
    except Exception:
        pass

    try:
        close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close")))
        close_button.click()
    except Exception:
        pass

    time.sleep(2)

    button = driver.find_element(By.CSS_SELECTOR, ".btn.btn-success")
    button.click()

    try:
        image_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "excelImg"))
        )
        image_element.click()

        time.sleep(15)

        files = os.listdir(base_directory)
        files = [f for f in files if f.endswith('.xls')]
        if not files:
            raise FileNotFoundError("No Excel files found in the download directory.")

        latest_file = max([os.path.join(base_directory, f) for f in files], key=os.path.getctime)
        fromdate = fromdate.replace("/", "-")
        todate = todate.replace("/", "-")

        new_file_name = os.path.join(scheme_directory, f"{scheme}_{fromdate}_to_{todate}_report.xls")

        shutil.move(latest_file, new_file_name)

        # print(f"Excel file for {scheme} downloaded and saved to {new_file_name}")
        table_name = 'CaseSearch'
        process_excel_file_and_upload(new_file_name, table_name)

        return new_file_name  # Return the path of the downloaded file

    except TimeoutException:
        print("No records found on the page.")
        return "no_records"


def process_excel_file_and_upload(file_path, table_name):
    try:
        # Read the Excel file without headers (header=None)
        df = pd.read_excel(file_path, header=None, engine='xlrd')

        # Set the column names to be the second row
        df.columns = df.iloc[2]

        # Remove the first two rows: the old header row and the new header row
        df = df[3:]
        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # Reset index to start from 0 after row removal
        df.reset_index(drop=True, inplace=True)

        # Replace NaN with None to handle missing values for MySQL
        df = df.where(pd.notnull(df), None)

        # Get updated column names from the new header row
        columns = df.columns.tolist()
        print(columns)

        # Create the table if it does not exist
        create_table_if_not_exists(table_name, columns)

        # Insert data into the table
        with connection.cursor() as cursor:
            for _, row in df.iterrows():
                # Prepare the data to match the number of columns
                row_data = tuple(row[col] for col in columns)

                # Check for redundancy
                placeholders = ' AND '.join([f'`{col}` = %s' for col in columns])
                check_sql = f'SELECT COUNT(*) FROM `{table_name}` WHERE {placeholders}'
                cursor.execute(check_sql, row_data)
                redundancy_count = cursor.fetchone()[0]

                if redundancy_count == 0:  # If no redundancy, proceed with insertion
                    # Construct the SQL query to insert data
                    placeholders = ', '.join(['%s'] * len(columns))  # Properly format placeholders
                    column_names = ', '.join([f'`{col}`' for col in columns])  # Use backticks for column names
                    sql = f'INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})'

                    # Execute the SQL query with the row values
                    cursor.execute(sql, row_data)

        print(f"Data uploaded to the table '{table_name}' successfully.")
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")



def create_table_if_not_exists(table_name, columns):
    # Generate the SQL to create a table dynamically, using backticks for MySQL compatibility
    column_definitions = ', '.join([f'`{col}` TEXT' for col in columns])  # Use backticks for column names
    create_table_sql = f'CREATE TABLE IF NOT EXISTS `{table_name}` (id INT PRIMARY KEY AUTO_INCREMENT, {column_definitions})'

    with connection.cursor() as cursor:
        cursor.execute(create_table_sql)
        print(f"Table '{table_name}' created or already exists.")


def drop_table(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        print(f"Table: {table_name} is deleted successfully")

def close_driver(driver):
    driver.switch_to.default_content()
    try:
        logout = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'VAGUS HOSPITAL'))
        )
        logout.click()

        # Wait for the 'Log Out' button to be clickable and click it
        logout_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, 'Log Out'))
        )
        logout_button.click()
        time.sleep(5)
    except Exception:
        pass

    driver.quit()

def input_case_type_again(driver,case_type):
    Casetype = driver.find_element(By.ID, "select2-caseType-container")
    Casetype.click()
    time.sleep(2)
    input_element = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
    input_element.send_keys(case_type, Keys.ENTER)


def mis_report(driver, scheme, intervals, request):
    # Initialize directories
    base_directory = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
    scheme_directory = os.path.join(base_directory, scheme)

    if not os.path.exists(scheme_directory):
        os.makedirs(scheme_directory)

    # Initialize variables
    downloaded_files = []  # Store all downloaded file paths
    count = 0
    menu_toggle = driver.find_element(By.ID, "menu_toggle")
    menu_toggle.click()
    mis_element = driver.find_element(By.XPATH, "//span[contains(text(), 'MIS')]")
    mis_element.click()
    claim_paid_report_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Claim Paid Report')]")
    claim_paid_report_element.click()
    iframe = WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "middleFrame"))
    )
    scheme_options = get_schemes(driver)
    schemes_to_process = scheme_options if scheme == "ALL" else [scheme]

    # WebDriverWait instance
    wait = WebDriverWait(driver, 5)

    for current_scheme in schemes_to_process:
        print(f"Processing scheme: {current_scheme}")
        input_scheme(driver, current_scheme)  # Input scheme name

        # Loop through date intervals
        for fromdate, todate in intervals:
            fromdateinputmis(driver, fromdate)
            todateinputmis(driver, todate)
            print(f"Processing interval: {fromdate} to {todate}")

            time.sleep(3)  # Adjust as necessary for page load

            try:
                # Attempt to close any modals if present
                try:
                    close_button = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close"))
                    )
                    close_button.click()
                    print("Close button clicked successfully!")
                except Exception:
                    print("No close button appeared.")

                # Download the Excel report
                try:
                    file_path = download_excel_mis(driver, current_scheme, fromdate, todate)
                    if file_path and os.path.exists(file_path) and file_path.endswith(".xls"):
                        downloaded_files.append(file_path)
                        count += 1
                        print(f"File downloaded and saved at {file_path}")
                    else:
                        print("No records found for the given interval.")

                except NoSuchElementException:
                    print("No records found.")
                    continue

            except Exception as e:
                print(f"Error occurred: {e}")
                continue
    driver.switch_to.default_content()
    # Combine downloaded files if any
    if downloaded_files:
        combined_file_path = combine_xls_files_mis(request, downloaded_files, scheme)
        print(f"Files combined and saved at {combined_file_path}")

        # Delete individual files after combining
        for file_path in downloaded_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted individual file: {file_path}")
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")

        # Store only the combined file path in the session
        request.session['downloaded_files'] = [combined_file_path]
        return combined_file_path  # Return the combined file path

    # If no records were found
    if count == 0:
        return "no_records"

    return "success"




def fromdateinput(driver, fromdate):
    date_input = driver.find_element(By.ID, 'advFromDate')

    # Custom date you want to set
    custom_date = fromdate  # Use your desired date in yyyy-mm-dd format

    # Use execute_script to set the value directly (bypassing the readonly attribute)
    driver.execute_script("arguments[0].removeAttribute('readonly')", date_input)  # Remove readonly attribute
    date_input.clear()
    date_input.send_keys(custom_date, Keys.ENTER)
    time.sleep(2)# Set the date using send_keys()
    wait = WebDriverWait(driver, 5)  # Adjust timeout as needed
    try:
        # Wait for the button to be visible and clickable
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.bootbox-accept")))
        button.click()
        print("Button clicked successfully!")
    except Exception as e:
        print(e)


def fromdateinputmis(driver, date_value):
    try:
        # Locate the 'fromDate' input field
        from_date_element = driver.find_element(By.ID, "fromDate")

        # Clear the field completely (backspaces multiple times)
        from_date_element.clear()
        time.sleep(0.2)
        for _ in range(10):  # Extra clearing in case the field doesn't fully clear
            from_date_element.send_keys(Keys.BACK_SPACE)

        # Ensure the field is empty before typing
        from_date_element.clear()

        # Send the date character by character with a delay
        for char in date_value:
            from_date_element.send_keys(char)
            time.sleep(0.05)  # Slight delay to mimic human typing

        # Optionally hit enter
        # from_date_element.send_keys(Keys.ENTER)

        # Verify the input matches what was intended
        entered_value = from_date_element.get_attribute("value")
        if entered_value != date_value:
            print(f"Retrying date input. Current value: {entered_value}")
            from_date_element.clear()
            from_date_element.send_keys(date_value, Keys.ENTER)

        print(f"Successfully entered 'From Date' as: {date_value}")

        # Wait for any modals or buttons if needed
        wait = WebDriverWait(driver, 5)  # Adjust timeout as needed
        try:
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.bootbox-accept")))
            button.click()
            print("Button clicked successfully!")
        except Exception as e:
            pass  # Ignore if button is not needed

    except Exception as e:
        print(f"Error while entering 'From Date': {str(e)}")
def todateinput(driver, todate):
    wait = WebDriverWait(driver, 5)  # Adjust timeout as needed
    try:
        # Wait for the button to be visible and clickable
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.bootbox-accept")))
        button.click()
        print("Button clicked successfully!")
    except Exception as e:
        print(e)

    to_date_input = driver.find_element(By.ID, 'advToDate')

    custom_date = todate

    # Use execute_script to remove the readonly attribute
    driver.execute_script("arguments[0].removeAttribute('readonly')", to_date_input)
    to_date_input.clear()
    # Click the input field after removing readonly
    # to_date_input.click()
    to_date_input.send_keys(custom_date, Keys.ENTER)  # Set the date using send_keys()
    wait = WebDriverWait(driver, 5)
    try:
        # Wait for the close button to be visible and clickable
        close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close")))
        close_button.click()
        print("Close button clicked successfully!")
    except Exception as e:
        print()  # Set the date using send_keys()


def todateinputmis(driver, date_value):
    try:
        # Locate the 'toDate' input field
        to_date_element = driver.find_element(By.ID, "toDate")

        # Explicitly wait for the element to be visible and interactable
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of(to_date_element))

        # Clear the input field by sending backspace repeatedly
        to_date_element.clear()  # Try clearing the field first
        time.sleep(0.2)  # Small delay after clearing
        for i in range(10):  # Send additional BACK_SPACE keys for extra clearing
            to_date_element.send_keys(Keys.BACK_SPACE)

        # Give a short delay to ensure clearing is processed
        time.sleep(0.5)

        # Send the new date value character by character with a short delay
        for char in date_value:
            to_date_element.send_keys(char)
            time.sleep(0.1)  # Slight delay between key presses to simulate human input

        # Optionally, send the ENTER key after inputting the date
        to_date_element.send_keys(Keys.ENTER)

        # Optionally wait to confirm the field was populated
        time.sleep(0.5)  # Short wait after entering the value

        print(f"Successfully entered 'To Date' as: {date_value}")

    except Exception as e:
        print(f"Error while entering 'To Date': {str(e)}")
def process_dates_and_download(driver, intervals, scheme, request):
    # Initialize an empty list to collect all downloaded file paths
    downloaded_files = []
    count = 0
    selected_option = "Registered Date"  # Hardcoding the option name here
    date_type_value = "ADS92"  # Hardcoding the value for "Registered Date"
    scheme_options = get_schemes(driver)

    # If scheme is "ALL", process for each scheme in the list
    schemes_to_process = scheme_options if scheme == "ALL" else [scheme]

    # Loop through the schemes
    for current_scheme in schemes_to_process:
        print(f"Processing scheme: {current_scheme}")
        input_scheme(driver,current_scheme)
    # Loop through date intervals
        for fromdate, todate in intervals:
            # Input the dates into the form
            fromdateinput(driver, fromdate)
            todateinput(driver, todate)
            print(f"Processing interval: {fromdate} to {todate}")

            time.sleep(3)  # Adjust as necessary for the page load

            try:
                print(f"Selected: {selected_option}")

                # Close any modal window that appears
                wait1 = WebDriverWait(driver, 5)
                try:
                    close_button = wait1.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close"))
                    )
                    close_button.click()
                    print("Close button clicked successfully!")
                except Exception:
                    pass  # Ignore if no close button appears

                # Download the file and store its path
                try:
                    file_path = download_excel1(driver, scheme,fromdate, todate)
                    if file_path and os.path.exists(file_path) and file_path.endswith(".xls"):
                        downloaded_files.append(file_path)
                        count += 1
                        print(f"File for {selected_option} downloaded and saved at {file_path}")
                    else:
                        print(f"No records found for {selected_option}.")

                except NoSuchElementException:
                    print("No records found for this option.")
                    pass

            except Exception as e:
                print(f"Error: {e}")
                continue

    if downloaded_files:
        # Combine the files after all downloads are complete
        combined_file_path = combine_xls_files(request,downloaded_files, scheme)
        print(f"Files combined and saved at {combined_file_path}")
        for file_path in downloaded_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted individual file: {file_path}")
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")
        # Update session to store only the combined file path
        request.session['downloaded_files'] = [combined_file_path]  # Store only the combined file path
        return combined_file_path  # Return the path to the combined file

    if count == 0:
        return "no_records"

    return "success"


def combine_xls_files(request,file_paths, scheme):
    # Create a new workbook to combine all sheets
    base_directory = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
    combined_wb = xlwt.Workbook()
    combined_sheet = combined_wb.add_sheet('Combined')
    fromdate = request.session.get('fromdate')
    todate = request.session.get('todate')
    fromdate = fromdate.replace("/", "-")
    todate = todate.replace("/", "-")
    current_row = 0
    for file_path in file_paths:
        # Open each .xls file
        wb = xlrd.open_workbook(file_path)
        sheet = wb.sheet_by_index(0)  # Assuming data is in the first sheet

        # Copy each row from the current file to the combined file
        for row_idx in range(sheet.nrows):
            for col_idx in range(sheet.ncols):
                combined_sheet.write(current_row, col_idx, sheet.cell_value(row_idx, col_idx))
            current_row += 1

    # Save the combined .xls file with a name based on the scheme
    combined_file_path = os.path.join(base_directory,f"{scheme}_combined_{fromdate}_to_{todate}.xls")
    combined_wb.save(combined_file_path)

    return combined_file_path


def combine_xls_files_mis(request,file_paths, scheme):
    # Create a new workbook to combine all sheets
    base_directory = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
    combined_wb = xlwt.Workbook()
    combined_sheet = combined_wb.add_sheet('Combined')
    fromdate = request.session.get('fromdate')
    todate = request.session.get('todate')
    fromdate = fromdate.replace("/", "-")
    todate = todate.replace("/", "-")
    current_row = 0
    for file_path in file_paths:
        # Open each .xls file
        wb = xlrd.open_workbook(file_path)
        sheet = wb.sheet_by_index(0)  # Assuming data is in the first sheet

        # Copy each row from the current file to the combined file
        for row_idx in range(sheet.nrows):
            for col_idx in range(sheet.ncols):
                combined_sheet.write(current_row, col_idx, sheet.cell_value(row_idx, col_idx))
            current_row += 1

    # Save the combined .xls file with a name based on the scheme
    combined_file_path = os.path.join(base_directory,f"{scheme}_scheme_combined_claim_paid_{fromdate}_to_{todate}.xls")
    combined_wb.save(combined_file_path)

    return combined_file_path
def get_90_day_intervals(start_date_str, end_date_str):
    # Convert string dates to datetime objects (assuming format is 'dd/mm/yyyy')
    start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
    end_date = datetime.strptime(end_date_str, '%d/%m/%Y')

    intervals = []

    # Loop to create 90-day intervals
    while start_date < end_date:
        next_date = start_date + timedelta(days=89)
        if next_date > end_date:
            next_date = end_date

        # Append the intervals in string format (dd/mm/yyyy)
        intervals.append((start_date.strftime('%d/%m/%Y'), next_date.strftime('%d/%m/%Y')))

        # Move start_date to the next interval
        start_date = next_date

    return intervals


def get_90_day_intervals_mis(start_date_str, end_date_str):
    # Convert string dates to datetime objects (assuming format is 'dd-mm-yyyy')
    start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
    end_date = datetime.strptime(end_date_str, '%d-%m-%Y')

    intervals = []

    # Loop to create 90-day intervals
    while start_date < end_date:
        next_date = start_date + timedelta(days=89)
        if next_date > end_date:
            next_date = end_date

        # Append the intervals in string format (dd-mm-yyyy)
        intervals.append((start_date.strftime('%d-%m-%Y'), next_date.strftime('%d-%m-%Y')))

        # Move start_date to the next interval
        start_date = next_date + timedelta(days=1)  # Move to the next day after the current interval

    return intervals


def get_schemes(driver):
    try:
        # Locate the dropdown element (select box)
        dropdown = Select(driver.find_element(By.ID, "selectedScheme"))

        # Extract all options from the dropdown
        options = dropdown.options

        # Get the values of the options (excluding invalid ones like "---select---")
        scheme_options = [option.get_attribute("value") for option in options if option.get_attribute("value") != "-1"]

        return scheme_options

    except Exception as e:
        print(f"Error extracting scheme options: {str(e)}")
        return []

def download_excel_mis(driver, scheme, fromdate, todate):
    # Set up directories
    base_directory = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
    scheme_directory = os.path.join(base_directory, scheme)

    if not os.path.exists(scheme_directory):
        os.makedirs(scheme_directory)

    wait = WebDriverWait(driver, 5)

    # Attempt to click any primary button (if present)
    try:
        button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.bootbox-accept"))
        )
        button.click()
    except Exception:
        pass  # Ignore if the button isn't found

    # Attempt to close any modal popups
    try:
        close_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close"))
        )
        close_button.click()
    except Exception:
        pass  # Ignore if no close button appears

    # Wait briefly before proceeding
    time.sleep(2)

    # Trigger the Excel download
    driver.find_element(By.CSS_SELECTOR, ".btn.btn-success").click()

    try:
        # Wait for the Excel image (download indicator) to be present and clickable
        image_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "excelImg"))
        )
        image_element.click()

        time.sleep(15)  # Give time for the download to complete

        # Fetch the latest downloaded file
        files = [f for f in os.listdir(base_directory) if f.endswith('.xls')]
        if not files:
            raise FileNotFoundError("No Excel files found in the download directory.")

        latest_file = max(
            [os.path.join(base_directory, f) for f in files], key=os.path.getctime
        )

        # Prepare the new file name
        fromdate = fromdate.replace("/", "-")
        todate = todate.replace("/", "-")
        new_file_name = os.path.join(scheme_directory, f"{scheme}_{fromdate}_to_{todate}_report.xls")

        # Move the downloaded file to the scheme-specific directory
        shutil.move(latest_file, new_file_name)

        print(f"Excel file for {scheme} downloaded and saved to {new_file_name}")
        table_name = 'ClaimPaid'
        # Process and upload the Excel file
        process_excel_file_and_upload(new_file_name, table_name)

        return new_file_name  # Return the path of the downloaded file

    except TimeoutException:
        print("No records found on the page.")
        return "no_records"


def refresh_captcha(driver):
    time.sleep(2)  # Adjust this if necessary for your page load time

    try:
        # Find the refresh link element by ID and click it
        refresh_link = driver.find_element(By.LINK_TEXT, 'refresh')
        refresh_link.click()
        print("Captcha refresh link clicked successfully.")
        time.sleep(5)
        captcha_download(driver)
    except Exception as e:
        print(f"An error occurred: {e}")