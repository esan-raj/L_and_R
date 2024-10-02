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


download_dir = os.path.join(os.path.dirname(__file__), 'Downloaded_documents')
def initialize_driver():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current file
    driver_path = os.path.join(base_dir, 'drivers', 'chromedriver.exe')
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
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--window-size=1920x1080")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")

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
    try:
        skip_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'skipBtn'))
        )
        time.sleep(2)  # Add a short delay to ensure the button is fully ready
        skip_button.click()
    except Exception as e:
        pass

def input_case_type(driver, case_type):
    iframe = driver.find_element(By.ID, "middleFrame")
    driver.switch_to.frame(iframe)
    # time.sleep(2)
    Casetype = driver.find_element(By.ID, "select2-caseType-container")
    Casetype.click()
    time.sleep(2)
    input_element = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
    input_element.send_keys(case_type, Keys.ENTER)

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


def download_excel1(driver, scheme, selected_option, fromdate, todate):
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

        new_file_name = os.path.join(scheme_directory, f"{scheme}_{selected_option}_report_{fromdate}_to_{todate}.xls")

        shutil.move(latest_file, new_file_name)

        print(f"Excel file for {scheme} downloaded and saved to {new_file_name}")
        process_excel_file_and_upload(new_file_name, scheme)

        return new_file_name  # Return the path of the downloaded file

    except TimeoutException:
        print("No records found on the page.")
        return "no_records"


def process_excel_file_and_upload(file_path, table_name):
    try:
        # Read the Excel file without headers (header=None)
        # drop_table(table_name)
        df = pd.read_excel(file_path, header=None, engine='xlrd')

        # Set the column names to be the second row
        df.columns = df.iloc[2]

        # Remove the first two rows: the old header row and the new header row
        df = df[3:]
        if 'index' in df.columns:
            df = df.drop(columns=['index'])

        # Reset index to start from 0 after row removal
        df.reset_index(drop=True, inplace=True)

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
                placeholders = ' AND '.join([f'"{col}" = %s' for col in columns])
                check_sql = f'SELECT COUNT(*) FROM "{table_name}" WHERE {placeholders}'
                cursor.execute(check_sql, row_data)
                redundancy_count = cursor.fetchone()[0]

                if redundancy_count == 0:  # If no redundancy, proceed with insertion
                    # Construct the SQL query to insert data
                    placeholders = ', '.join(['%s'] * len(columns))  # Properly format placeholders
                    column_names = ', '.join([f'"{col}"' for col in columns])  # Properly quote column names
                    sql = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'

                    # Execute the SQL query with the row values
                    cursor.execute(sql, row_data)

        print(f"Data uploaded to the table '{table_name}' successfully.")
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")


def create_table_if_not_exists(table_name, columns):
    # Generate the SQL to create a table dynamically
    column_definitions = ', '.join([f'"{col}" TEXT' for col in columns])  # Ensure column names are properly quoted
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (id INTEGER PRIMARY KEY AUTOINCREMENT, {column_definitions})'

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

def mis_report (driver,scheme):
    menu_toggle = driver.find_element(By.ID, "menu_toggle")
    menu_toggle.click()
    mis_element = driver.find_element(By.XPATH, "//span[contains(text(), 'MIS')]")
    mis_element.click()
    claim_paid_report_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Claim Paid Report')]")
    claim_paid_report_element.click()
    iframe = WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "middleFrame"))
    )
    Scheme = driver.find_element(By.ID, "select2-selectedScheme-container")
    Scheme.click()
    input_element = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
    # Set the value
    input_element.send_keys(scheme, Keys.ENTER)
    button = driver.find_element(By.CSS_SELECTOR, ".btn.btn-success")
    button.click()
    mis_report = driver.find_element(By.ID, "excelImg")
    mis_report.click()
    driver.switch_to.default_content()


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
        print()


def todateinput(driver, todate):
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


def process_dates_and_download(driver, intervals, scheme, request):
    # Loop through date intervals
    downloaded_files = []  # Collect all downloaded file paths here
    count = 0
    for fromdate, todate in intervals:
        # Pass the dates to the input functions
        fromdateinput(driver, fromdate)
        todateinput(driver, todate)
        print(f"Processing interval: {fromdate} to {todate}")

        # Loop through each option in the dropdown
        for index in range(1, len(Select(driver.find_element(By.ID, 'dateType')).options)):
            time.sleep(3)

            try:
                # Re-locate the dropdown and select the option by index
                dropdown = Select(driver.find_element(By.ID, 'dateType'))
                dropdown.select_by_index(index)
                time.sleep(5)

                # Perform your tasks here
                selected_option = dropdown.options[index].text
                print(f"Selected: {selected_option}")

                # Handle the close button if it appears
                wait1 = WebDriverWait(driver, 5)
                try:
                    close_button = wait1.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-close-button.close")))
                    close_button.click()
                    print("Close button clicked successfully!")
                except Exception:
                    pass  # If the button doesn't appear, skip

                # Try to find the image element and click it if it exists
                try:
                    # Call download_excel function to download the file
                    file_path = download_excel1(driver, scheme, selected_option, fromdate, todate)
                    if file_path and os.path.exists(file_path):
                        downloaded_files.append(file_path)
                        count += 1
                        print(f"File for {selected_option} downloaded and saved at {file_path}")
                    else:
                        print(f"No records found for {selected_option}.")

                except NoSuchElementException:
                    print("NO records found for this option.")
                    pass

            except StaleElementReferenceException:
                # Handle stale element reference exception, re-fetch the element
                print("StaleElementReferenceException: Re-fetching the element...")
                dropdown = Select(driver.find_element(By.ID, 'dateType'))
                continue

    if count == 0:
        return "no_records"

    # Store the list of downloaded files in the session
    request.session['downloaded_files'] = downloaded_files
    return "success"



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