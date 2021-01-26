import unittest
from selenium import webdriver
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()
class TestLogin(TestCase):
    def setUp(self):
        # NOTE: change PATH to a local path that has your downloaded chromedriver.exe
        PATH = '/Users/hcr/Downloads/chromedriver'
        self.driver = webdriver.Chrome(PATH)
        # set up a user
        user1 = User(username='user1')
        user1_pw = 'test-user1-pwd'
        user1.set_password(user1_pw)
        user1.is_staff = True
        user1.is_superuser = True
        user1.save()
        self.user1_pw = user1_pw
        self.user2_pw = 'test-user2-pwd'
        # some urls
        self.base_url = "http://127.0.0.1:8000/"
        self.login_url = self.base_url + "accounts/login/"
        self.register_url = self.base_url + "register/"


    # fill in correct username and correct password
    def test_login_1(self):
        self.driver.get(self.login_url)
        self.driver.find_element_by_id('id_username').send_keys("user1")
        self.driver.find_element_by_id('id_password').send_keys(self.user1_pw)
        self.driver.find_element_by_id('login_button').click()
        self.assertIn(self.base_url, self.driver.current_url)
    
    # fill in correct username and incorrect password
    def test_login_2(self):
        self.driver.get(self.login_url)
        self.driver.find_element_by_id('id_username').send_keys("user1")
        self.driver.find_element_by_id('id_password').send_keys("test12345678")
        self.driver.find_element_by_id('login_button').click()
        self.assertIn(self.login_url, self.driver.current_url)

    # fill in unused username and safe password
    def test_register_1(self):
        self.driver.get(self.register_url)
        self.driver.find_element_by_id('id_username').send_keys("user2")
        self.driver.find_element_by_id('id_password1').send_keys(self.user2_pw)
        self.driver.find_element_by_id('id_password2').send_keys(self.user2_pw)
        self.driver.find_element_by_id('register_button').click()
        self.assertIn(self.base_url, self.driver.current_url)
    
    # fill in duplicate username and safe password
    def test_register_2(self):
        self.driver.get(self.register_url)
        self.driver.find_element_by_id('id_username').send_keys("user1")
        self.driver.find_element_by_id('id_password1').send_keys(self.user2_pw)
        self.driver.find_element_by_id('id_password2').send_keys(self.user2_pw)
        self.driver.find_element_by_id('register_button').click()
        self.assertIn(self.register_url, self.driver.current_url)

    # fill in unused username but unsafe password
    def test_register_3(self):
        self.driver.get(self.register_url)
        self.driver.find_element_by_id('id_username').send_keys("user1")
        self.driver.find_element_by_id('id_password1').send_keys("12345678")
        self.driver.find_element_by_id('id_password2').send_keys("12345678")
        self.driver.find_element_by_id('register_button').click()
        self.assertIn(self.register_url, self.driver.current_url)
    
    # fill in unused username and safe password, but wrong password in confirmation
    def test_register_4(self):
        self.driver.get(self.register_url)
        self.driver.find_element_by_id('id_username').send_keys("user1")
        self.driver.find_element_by_id('id_password1').send_keys(self.user2_pw)
        self.driver.find_element_by_id('id_password2').send_keys("12345678")
        self.driver.find_element_by_id('register_button').click()
        self.assertIn(self.register_url, self.driver.current_url)

    def tearDown(self):
        self.driver.quit()