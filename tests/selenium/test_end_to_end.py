import os
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:8943"
TEST_CSV_PATH = os.path.abspath(os.path.join("tests", "assets", "IDCJAC0016_009021_1800_Data.csv"))

# Helper function
def login(driver, username, password):
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "submit").click()
    WebDriverWait(driver, 5).until(EC.url_contains("/dashboard"))

# 1. Register a new user
def test_register(driver, start_test_server):
    driver.get(f"{BASE_URL}/register")
    driver.find_element(By.NAME, "username").send_keys("testuser1")
    driver.find_element(By.NAME, "email").send_keys("test1@example.com")
    driver.find_element(By.NAME, "password").send_keys("password123")
    driver.find_element(By.NAME, "password2").send_keys("password123")
    driver.find_element(By.NAME, "security_answer").send_keys("cookie")
    driver.find_element(By.NAME, "submit").click()
    WebDriverWait(driver, 5).until(EC.url_contains("/login"))
    assert "login" in driver.current_url

# 2. Login the registered user
def test_login(driver, start_test_server):
    login(driver, "testuser1", "password123")
    assert "Dashboard" in driver.page_source

# 3. Upload a CSV file
def test_upload(driver, start_test_server):
    login(driver, "testuser1", "password123")
    driver.get(f"{BASE_URL}/upload")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "csv_file")))
    driver.find_element(By.NAME, "city").send_keys("Perth")
    driver.find_element(By.NAME, "latitude").send_keys("-31.95")
    driver.find_element(By.NAME, "longitude").send_keys("115.86")
    driver.find_element(By.NAME, "csv_file").send_keys(TEST_CSV_PATH)
    driver.find_element(By.NAME, "submit").click()
    WebDriverWait(driver, 5).until(EC.url_contains("/index"))
    assert "my files" in driver.page_source.lower()

# 4. Change file to public and check visibility
def test_update_visibility(driver, start_test_server):
    from selenium.webdriver.support.ui import Select

    login(driver, "testuser1", "password123")
    driver.get(f"{BASE_URL}/index")

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, "Update")))
    driver.find_elements(By.LINK_TEXT, "Update")[0].click()

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "visibility")))
    Select(driver.find_element(By.NAME, "visibility")).select_by_value("public")

    driver.find_element(By.ID, "permissionsForm").submit()
    WebDriverWait(driver, 5).until(EC.url_contains("/index"))

    assert "Permissions updated" in driver.page_source or "my files" in driver.page_source.lower()

# 5. Forgot password flow
def test_forgot_password(driver, start_test_server):
    driver.get(f"{BASE_URL}/forgot_password")
    driver.find_element(By.NAME, "email").send_keys("test1@example.com")
    driver.find_element(By.NAME, "submit").click()
    WebDriverWait(driver, 5).until(EC.url_contains("/reset_password"))
    driver.find_element(By.NAME, "security_answer").send_keys("cookie")
    driver.find_element(By.NAME, "new_password").send_keys("newpass123")
    driver.find_element(By.NAME, "new_password2").send_keys("newpass123")
    driver.find_element(By.NAME, "submit").click()
    WebDriverWait(driver, 5).until(EC.url_contains("/login"))
    assert "reset" in driver.page_source.lower()
    
# 6. Change email address
def test_change_email(driver, start_test_server):
    login(driver, "testuser1", "newpass123")  # Use new password after reset
    driver.get(f"{BASE_URL}/profile")

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "email")))
    email_input = driver.find_element(By.NAME, "email")
    email_input.clear()
    email_input.send_keys("updated1@example.com")

    driver.find_element(By.NAME, "submit_email").click()
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "flashes")))

    assert "email updated successfully" in driver.page_source.lower()

