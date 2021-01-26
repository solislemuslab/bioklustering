import unittest
from selenium import webdriver
from django.test import TestCase

class TestLogin(unittest.TestCase):
    def setUp(self):
        # a local path that has your downloaded chromedriver.exe
        PATH = '/Users/hcr/Downloads/chromedriver'
        self.driver = webdriver.Chrome(PATH)

    def test_login_fire(self):
        self.driver.get("http://127.0.0.1:8000/accounts/login")
        self.driver.find_element_by_id('id_username').send_keys("user1")
        self.driver.find_element_by_id('id_password').send_keys("test-user1-pwd")
        self.driver.find_element_by_id('login_button').click()
        self.assertIn("http://127.0.0.1:8000/", self.driver.current_url)

    def tearDown(self):
        self.driver.quit()

    if __name__ == '__main__':
        unittest.main()
