import base64
import io
import shutil
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from PIL import Image
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
from datetime import datetime
from .models import AppUser  # Import the AppUser model

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


download_dir = r'D:\practice_project\L&R_redesign\Downloaded_documents'
def initialize_driver():
    driver_path = r'C:\Users\Esan Raj\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
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
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://tmsreports.pmjay.gov.in/OneTMS/loginnew.htm")
    return driver

def login_site(driver,site_username, site_password):
    username_field = driver.find_element(By.NAME, 'username')
    username_field.send_keys(site_username)
    process = driver.find_element(By.ID, 'proceed')
    process.click()
    time.sleep(10)
    close_button = driver.find_element(By.CLASS_NAME, 'bootbox-close-button')
    close_button.click()
    password_field = driver.find_element(By.NAME, 'password')
    password_field.send_keys(site_password)
    captcha_download(driver)

# def navigate_to_form(driver):
#     captcha_img = driver.find_element(By.ID, 'captchaImg')
#     captcha_src = captcha_img.get_attribute('src')
#     return captcha_src
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

def download_excel(driver,scheme):
    base_directory = r"D:\practice_project\L&R_redesign\Downloaded_documents" # Already set in Chrome options
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
            EC.presence_of_element_located((By.ID, "excelImg")))
        # If the element is found, click it to download the Excel file
        image_element.click()
        time.sleep(15)  # Wait for the download to complete
        files = os.listdir(base_directory)
        files = [f for f in files if f.endswith('.xls')]
        if not files:
            raise FileNotFoundError("No Excel files found in the download directory.")

        latest_file = max([os.path.join(base_directory, f) for f in files], key=os.path.getctime)

        # Destination path in the scheme-specific subdirectory
        new_file_name = os.path.join(scheme_directory, f"{scheme}_report{timestamp}.xls")

        # Move the file to the scheme-specific directory and rename it
        shutil.move(latest_file, new_file_name)

        print(f"Excel file for {scheme} downloaded and saved to {new_file_name}")
        return "success"
          # Return success status
    except TimeoutException:
        print("No records found on the page.")
        return "no_records"  # Return no records status

def close_driver(driver):
    driver.switch_to.default_content()
    logout = driver.find_element(By.PARTIAL_LINK_TEXT, 'VAGUS HOSPITAL')
    logout.click()
    time.sleep(2)
    logout_button = driver.find_element(By.LINK_TEXT, 'Log Out')
    logout_button.click()
    time.sleep(10)
    driver.quit()

def input_case_type_again(driver,case_type):
    Casetype = driver.find_element(By.ID, "select2-caseType-container")
    Casetype.click()
    time.sleep(2)
    input_element = driver.find_element(By.CSS_SELECTOR, ".select2-search__field")
    input_element.send_keys(case_type, Keys.ENTER)