# Web Scraping Automation with Selenium

## Project Overview

This project is a web scraping automation tool built using Selenium in Python. It is designed to interact with a specific web portal, log in using user credentials, navigate through various selections, download Excel reports based on user input, and handle captcha verification.

## Features

- **Automated Login**: The script automates the login process, including captcha solving.
- **Dynamic Form Submission**: Allows selecting different options like scheme types and records periods from dropdowns.
- **Excel File Download**: Downloads Excel reports based on the selected inputs, storing each file in a specified directory.
- **Error Handling**: Manages scenarios where no records are found and handles any potential errors during the scraping process.
- **Headless Mode**: Optionally runs the Chrome browser in headless mode, keeping all operations in the background.

## Project Structure

- **`scraping.py`**: The main script containing all functions related to web scraping and automation.
- **`settings.py`**: Django settings file, including configurations for media files.
- **`urls.py`**: Django URL configurations, including paths for serving media files.
- **`models.py`**: Contains the `CustomUser` model and any other database models used in the project.
- **`templates/`**: Directory containing HTML templates, including the login page.
- **`media/captchas/`**: Directory where captcha images are stored.
- **`media/Downloaded_documents/`**: Directory where downloaded Excel files are stored, organized by scheme name and timestamp.

## Prerequisites

- **Python 3.x**
- **Selenium**: Installed via pip (`pip install selenium`)
- **ChromeDriver**: Make sure to download and place the correct version of ChromeDriver for your Chrome browser.
- **Django**: Installed via pip (`pip install django`)

## Setup and Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/esan-raj/Web_App.git
   cd Web_App
   
   
2. **Open the Project**
    ```sh
   cd Vagus

3. **Start the virtual environment and install dependencies**
    ````sh
   .venv/Scripts/activate
   pip install -r requirements.txt

4. **Update 'scraping.py'**
    * Set the driver_path to the location of your ChromeDriver[(for downloading compatible chromedriver [click here](https://googlechromelabs.github.io/chrome-for-testing/)).
    * Update download_dir to your desired directory for storing downloaded Excel files.

5. **Run the Django Project**
    ````sh
   python manage.py runserver
   
## Usage 

1. **Input Scheme:**

* Select a scheme using the dropdown menu, or manually input the scheme using the provided form.
* The tool will automatically submit the form, download the corresponding Excel report, and save it in the specified directory.

2. **Captcha Handling:**

* The tool will display a captcha image that needs to be solved manually (if not automated).
* Enter the captcha value and submit the form.

3. **Error Handling:**

* If no records are found for the selected scheme, a message will be displayed on the web page.

## Troubleshooting
1. **ChromeDriver Compatibility:**

* Ensure that the version of ChromeDriver matches your installed Chrome browser version.
* for downloading the compatible chromedriver please visit: https://googlechromelabs.github.io/chrome-for-testing/

2. **Timeouts:**

* If the script fails due to timeouts, consider increasing the wait time in WebDriverWait calls.

