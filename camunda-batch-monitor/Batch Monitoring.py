'''
import subprocess
import sys

# List of packages to install
packages = ['pywin32', 'webdriver-manager', 'selenium']

# Install packages using pip
for package in packages:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Successfully installed {package}")
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}")
'''
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import win32com.client as win32

# URL, credentials and other variables intialized
URL = 'https://localhost:8080/camunda/app/cockpit/default'
USERNAME = 'demo'
PASSWORD = 'demo'
PROCESS_ACTIVE = False
PROCESS_STATUS = ''
SCREENSHOT_PATH = 'screenshot.png'

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Start browser maximized
chrome_options.add_argument("--disable-notifications")  # Disable notifications
chrome_options.add_experimental_option("detach", True)  # Keep browser open after script finishes

# Initialize WebDriver using webdriver_manager to manage ChromeDriver automatically
driver = webdriver.Chrome(options=chrome_options)# webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

try:
    # Step 1: Open the Camunda Cockpit website
    driver.get(URL)
    
    # Step 2: Log in with username and password
    username_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' and @tabindex='1']"))
    )
    username_element.send_keys(USERNAME)
    
    password_element = driver.find_element(By.XPATH, "//input[@type='password' and @tabindex='2']")
    password_element.send_keys(PASSWORD)
    password_element.send_keys(Keys.RETURN)
    
    # Navigate to process list page
    driver.get(URL + "/#/processes")

    # Step 3: Wait for the process link to be available
    link_batchProcess_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "BatchProcess"))
    )
    
    # Step 4: Click the process link
    ActionChains(driver).move_to_element(link_batchProcess_element).click().perform()
    
    # Wait for Process to load
    time.sleep(5)
    
    # Step 5: Check if the process is active or completed
    if len(driver.find_elements(By.XPATH, "//div[contains(text(), 'No process instances matched by current filter')]")) == 0:
        # Active BatchProcess found
        PROCESS_ACTIVE = True
        PROCESS_STATUS = "BatchProcess"
        
        # Step 6: Click on the 'History' tab to view process history
        history_view_button = driver.find_element(By.XPATH, "//a[text()='History']")
        history_view_button.click()
        
        # Wait for History View to load
        time.sleep(3)
        
        # Step 7: Take a screenshot of the active process
        driver.save_screenshot(SCREENSHOT_PATH)
    
    else:
        # Step 8: Check for LmdBatchProcess if BatchProcess is not active
        driver.get(URL + "/#/processes")
        link_lmdBatchProcess_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "LmdBatchProcess"))
        )
        
        ActionChains(driver).move_to_element(link_lmdBatchProcess_element).click().perform()
        
        # Wait for Process to load
        time.sleep(5)
        
        # Step 9: Check if LmdBatchProcess is active or completed
        if len(driver.find_elements(By.XPATH, "//div[contains(text(), 'No process instances matched by current filter')]")) != 0:
            # Process is completed
            PROCESS_STATUS = "Batch Completed!"  # Prepare status for email
        else:
            # Active LmdBatchProcess found
            PROCESS_ACTIVE = True
            PROCESS_STATUS = "LmdBatchProcess"
            
        # Step 10: Click on the 'History' tab to view process history
        history_view_button = driver.find_element(By.XPATH, "//a[text()='History']")
        history_view_button.click()
        
        # Wait for History View to load
        time.sleep(3)
        
        # Step 11: Take a screenshot of the active process
        driver.save_screenshot(SCREENSHOT_PATH)
    
    # Step 12: Send the screenshot via Outlook email
    outlook = win32.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)  # Create a new mail item
    mail.Subject = 'Batch Process Status'
    mail.Body = f'Please find the attached screenshot of the Active process diagram - {PROCESS_STATUS}' if PROCESS_ACTIVE else PROCESS_STATUS
    mail.To = 'user1@example.com; user2@example.com'  # Add recipient email address here
    
    mail.Attachments.Add('C:/Users/ZX/Desktop/' + SCREENSHOT_PATH)  # Attach screenshot
    mail.Categories = "Batch Monitoring"
    mail.Save()
    #mail.Send()  # Send email
    print(PROCESS_STATUS)

finally:
    # Step 13: Close the browser
    driver.quit()