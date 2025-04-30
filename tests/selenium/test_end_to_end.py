import os
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app import create_app, db

@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "LIVESERVER_PORT": 8943,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "testkey"
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless")
    driver = WebDriver(service=Service(ChromeDriverManager().install()), options=options)
    yield driver
    driver.quit()

BASE_URL = "http://localhost:8943"

# ---------- Test 1: Register ----------
def test_register(driver, start_test_server):
    driver.get("http://localhost:8943/register")

    driver.find_element(By.NAME, "username").send_keys("admintest")
    driver.find_element(By.NAME, "email").send_keys("admintest@example.com")
    driver.find_element(By.NAME, "password").send_keys("admin123")
    driver.find_element(By.NAME, "password2").send_keys("admin123")
    driver.find_element(By.NAME, "security_answer").send_keys("saturn")
    driver.find_element(By.NAME, "submit").click()

    # You get redirected after registration
    assert "login" in driver.current_url.lower()

# ---------- Test 2: Login ----------
def test_login(driver, start_test_server):
    driver.get(BASE_URL + "/logout")  # Ensure logged out first
    driver.get(BASE_URL + "/login")
    driver.find_element(By.NAME, "username").send_keys("admintest")
    driver.find_element(By.NAME, "password").send_keys("admin123")
    driver.find_element(By.NAME, "submit").click()
    time.sleep(1)
    assert "Dashboard" in driver.page_source or "dashboard" in driver.current_url

# ---------- Test 3: Upload CSV ----------
def test_upload_csv(driver, start_test_server):
    driver.get("http://localhost:8943/upload")

    # Point to one of your actual test CSV files
    test_csv_path = os.path.abspath(os.path.join("tests", "assets", "IDCJAC0016_009021_1800_Data.csv"))
    driver.find_element(By.NAME, "csv_file").send_keys(test_csv_path)

    driver.find_element(By.NAME, "city").send_keys("PERTH")
    driver.find_element(By.NAME, "latitude").send_keys("-31.93")
    driver.find_element(By.NAME, "longitude").send_keys("115.98")
    driver.find_element(By.NAME, "submit").click()
    assert "your files" in driver.title.lower() or "index" in driver.current_url
