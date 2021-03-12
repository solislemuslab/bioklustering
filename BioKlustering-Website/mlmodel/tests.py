import os
import json
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from .models import FileInfo, FileListInfo, PredictInfo

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
test_file_1 = os.path.abspath(os.path.join(ROOT_DIR, "..", "..", "manuscript", "validation-data", "Semi-supervised-test-dataset", "combined_Bat_Cat_flu.fa"))
test_file_2 = os.path.abspath(os.path.join(ROOT_DIR, "..", "..", "manuscript", "validation-data", "Semi-supervised-test-dataset", "labels_fifty_percent.csv"))
webdriver_exe = os.path.abspath(os.path.join(ROOT_DIR, "..", "..", "chromedriver"))

User = get_user_model()

# test login and register behavior
class TestLoginAndRegisterView(StaticLiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # set up web driver
        cls.selenium = webdriver.Chrome(webdriver_exe)
        cls.selenium.implicitly_wait(10)
        # set up urls
        cls.login_url = cls.live_server_url + "/accounts/login/"
        cls.register_url = cls.live_server_url + "/register/"

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
    
    def setUp(self):
        # set up users
        user1 = User(username='user1')
        user1_pw = 'test-user1-pwd'
        user1.set_password(user1_pw)
        user1.is_staff = True
        user1.is_superuser = True
        user1.save()
        self.user1 = user1
        self.user1_pw = user1_pw
        self.user2_name = "user2"
        self.user2_pw = 'test-user2-pwd'

    # fill in correct username and correct password
    def test_login_1(self):
        self.selenium.get(self.login_url)
        self.selenium.find_element_by_id('id_username').send_keys(self.user1.get_username())
        self.selenium.find_element_by_id('id_password').send_keys(self.user1_pw)
        self.selenium.find_element_by_id('login_button').click()
        self.assertEqual(self.live_server_url+'/', self.selenium.current_url)
    
    # fill in correct username and incorrect password
    def test_login_2(self):
        self.selenium.get(self.login_url)
        self.selenium.find_element_by_id('id_username').send_keys(self.user1.get_username())
        self.selenium.find_element_by_id('id_password').send_keys("fgaecbaouef")
        self.selenium.find_element_by_id('login_button').click()
        self.assertEqual(self.login_url, self.selenium.current_url)

    # fill in unused username and safe password
    def test_register_1(self):
        self.selenium.get(self.register_url)
        self.selenium.find_element_by_id('id_username').send_keys(self.user2_name)
        self.selenium.find_element_by_id('id_password1').send_keys(self.user2_pw)
        self.selenium.find_element_by_id('id_password2').send_keys(self.user2_pw)
        self.selenium.find_element_by_id('register_button').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)

    # fill in unused username and safe password, but wrong password in confirmation
    def test_register_2(self):
        self.selenium.get(self.register_url)
        self.selenium.find_element_by_id('id_username').send_keys(self.user2_name)
        self.selenium.find_element_by_id('id_password1').send_keys(self.user2_pw)
        self.selenium.find_element_by_id('id_password2').send_keys("hoeuacobue")
        self.selenium.find_element_by_id('register_button').click()
        self.assertEqual(self.register_url, self.selenium.current_url)
    
    # fill in unused username but unsafe password
    def test_register_3(self):
        self.selenium.get(self.register_url)
        self.selenium.find_element_by_id('id_username').send_keys(self.user2_name)
        self.selenium.find_element_by_id('id_password1').send_keys("12345678")
        self.selenium.find_element_by_id('id_password2').send_keys("12345678")
        self.selenium.find_element_by_id('register_button').click()
        self.assertEqual(self.register_url, self.selenium.current_url)
        
    # fill in duplicate username and safe password
    def test_register_4(self):
        self.selenium.get(self.register_url)
        self.selenium.find_element_by_id('id_username').send_keys(self.user1.get_username())
        self.selenium.find_element_by_id('id_password1').send_keys(self.user2_pw)
        self.selenium.find_element_by_id('id_password2').send_keys(self.user2_pw)
        self.selenium.find_element_by_id('register_button').click()
        self.assertEqual(self.register_url, self.selenium.current_url)

# test upload file behavior
class TestUploadFilesView(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # set up web driver
        cls.selenium = webdriver.Chrome(webdriver_exe)
        cls.selenium.implicitly_wait(10)
        # set up urls
        cls.login_url = cls.live_server_url + "/accounts/login/"
        cls.register_url = cls.live_server_url + "/register/"

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        # set up users
        user1 = User(username='user1')
        user1_pw = 'test-user1-pwd'
        user1.set_password(user1_pw)
        user1.is_staff = True
        user1.is_superuser = True
        user1.save()
        # login user
        self.selenium.get(self.login_url)
        self.selenium.find_element_by_id('id_username').send_keys(user1.get_username())
        self.selenium.find_element_by_id('id_password').send_keys(user1_pw)
        self.selenium.find_element_by_id('login_button').click()
    
    def tearDown(self):
        filelist = FileListInfo.objects.last()
        if filelist:
            filelist.delete_files()

    # upload one sequence file
    def test_upload_file_1(self):
        # wait for page showing up
        wait_seq = WebDriverWait(self.selenium, 5)
        wait_seq.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_sequence"))).send_keys(test_file_1)
        # upload file
        self.selenium.find_element_by_id('file_upload_btn').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)
        self.assertEqual(FileInfo.objects.all().count(), 1)
        self.assertEqual(FileListInfo.objects.all().count(), 0)
        # add one file pair to filelist
        filelist = self.selenium.find_element_by_id("id_filelist_form-filelist_0").click()
        self.assertEqual(FileListInfo.objects.all().count(), 1)
    
    # upload one sequence and one label pair
    def test_upload_file_2(self):
        # wait for page showing up
        wait_seq = WebDriverWait(self.selenium, 5)
        wait_seq.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_sequence"))).send_keys(test_file_1)
        wait_label = WebDriverWait(self.selenium, 5)
        wait_label.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_label"))).send_keys(test_file_2)
        # upload file
        self.selenium.find_element_by_id('file_upload_btn').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)
        self.assertEqual(FileInfo.objects.all().count(), 1)
        self.assertEqual(FileListInfo.objects.all().count(), 0)
        # add one file pair to filelist
        filelist = self.selenium.find_element_by_id("id_filelist_form-filelist_0").click()
        self.assertEqual(FileListInfo.objects.all().count(), 1)
    

    # upload one label file
    def test_upload_file_3(self):
        # wait for page showing up
        wait_label = WebDriverWait(self.selenium, 5)
        wait_label.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_label"))).send_keys(test_file_2)
        # upload file
        self.selenium.find_element_by_id('file_upload_btn').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)
        self.assertEqual(FileInfo.objects.all().count(), 0)
        self.assertEqual(FileListInfo.objects.all().count(), 0)
        # upload file should fail so no files in the filelist
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element_by_id("id_filelist_form-filelist_0")
        self.assertEqual(FileListInfo.objects.all().count(), 0)
    
    # upload multiple sequence and label pair
    def test_upload_file_4(self):
        # ------- upload 1st pair -------
        # wait for page showing up
        wait_seq = WebDriverWait(self.selenium, 5)
        wait_seq.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_sequence"))).send_keys(test_file_1)
        wait_label = WebDriverWait(self.selenium, 5)
        wait_label.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_label"))).send_keys(test_file_2)
        # upload file
        self.selenium.find_element_by_id('file_upload_btn').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)
        self.assertEqual(FileInfo.objects.all().count(), 1)
        self.assertEqual(FileListInfo.objects.all().count(), 0)
        # add one file pair to filelist
        self.selenium.find_element_by_id("id_filelist_form-filelist_0").click()
        self.assertEqual(FileListInfo.objects.all().count(), 1)
        filelist_last = FileListInfo.objects.last()
        filelist = getattr(filelist_last, 'filelist', None)
        self.assertEqual(filelist.all().count(), 1)
        
        # ------- upload 2nd pair -------
        # wait for page showing up
        wait_seq = WebDriverWait(self.selenium, 5)
        wait_seq.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_sequence"))).send_keys(test_file_1)
        wait_label = WebDriverWait(self.selenium, 5)
        wait_label.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_label"))).send_keys(test_file_2)
        # upload file
        self.selenium.find_element_by_id('file_upload_btn').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)
        self.assertEqual(FileInfo.objects.all().count(), 2)
        # add one file pair to filelist
        self.selenium.find_element_by_id("id_filelist_form-filelist_1").click()
        filelist_last = FileListInfo.objects.last()
        filelist = getattr(filelist_last, 'filelist', None)
        self.assertEqual(filelist.all().count(), 2)

        # ------- upload 3rd pair -------
        # wait for page showing up
        wait_seq = WebDriverWait(self.selenium, 5)
        wait_seq.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_sequence"))).send_keys(test_file_1)
        wait_label = WebDriverWait(self.selenium, 5)
        wait_label.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#inputfile_label"))).send_keys(test_file_2)
        # upload file
        self.selenium.find_element_by_id('file_upload_btn').click()
        self.assertEqual(self.live_server_url + "/", self.selenium.current_url)
        self.assertEqual(FileInfo.objects.all().count(), 3)
        # add one file pair to filelist
        self.selenium.find_element_by_id("id_filelist_form-filelist_2").click()
        filelist_last = FileListInfo.objects.last()
        filelist = getattr(filelist_last, 'filelist', None)
        self.assertEqual(filelist.all().count(), 3)

        # ensure there is always 1 filelist
        self.assertEqual(FileListInfo.objects.all().count(), 1)

        
# test model select and parameter fill in
class TestModelSelect(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # set up web driver
        cls.selenium = webdriver.Chrome(webdriver_exe)
        cls.selenium.implicitly_wait(10)
        # set up urls
        cls.login_url = cls.live_server_url + "/accounts/login/"
        cls.register_url = cls.live_server_url + "/register/"

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        # set up users
        user1 = User(username='user1')
        user1_pw = 'test-user1-pwd'
        user1.set_password(user1_pw)
        user1.is_staff = True
        user1.is_superuser = True
        user1.save()
        # login user
        self.selenium.get(self.login_url)
        self.selenium.find_element_by_id('id_username').send_keys(user1.get_username())
        self.selenium.find_element_by_id('id_password').send_keys(user1_pw)
        self.selenium.find_element_by_id('login_button').click()
        # upload file
        self.selenium.find_element_by_id('inputfile_sequence').send_keys(test_file_1)
        self.selenium.find_element_by_id('inputfile_label').send_keys(test_file_2)
        self.selenium.find_element_by_id('file_upload_btn').click()
        # add one file pair to filelist
        self.selenium.find_element_by_id("id_filelist_form-filelist_0").click()
    
    def tearDown(self):
        filelist = FileListInfo.objects.last()
        if filelist:
            filelist.delete_files()
    
    # select kmeans and see if the underlying data get updated
    def test_model_select_1(self):
        select = Select(self.selenium.find_element_by_id('id_predict_form-mlmodels'))
        # select semisupervised kmeans
        select.select_by_index(1)
        predict_last = PredictInfo.objects.last()
        mlmodel = getattr(predict_last, 'mlmodels', None)
        self.assertEqual('semisupervisedKmeans', mlmodel)

    # select gmm and see if the underlying data get updated
    def test_model_select_2(self):
        select = Select(self.selenium.find_element_by_id('id_predict_form-mlmodels'))
        # select unsupervised gmm
        select.select_by_index(2)
        predict_last = PredictInfo.objects.last()
        mlmodel = getattr(predict_last, 'mlmodels', None)
        self.assertEqual('unsupervisedGMM', mlmodel)

    # select spectral clustering and see if the underlying data get updated
    def test_model_select_3(self):
        select = Select(self.selenium.find_element_by_id('id_predict_form-mlmodels'))
        # select semisupervised spectral clustering
        select.select_by_index(5)
        predict_last = PredictInfo.objects.last()
        mlmodel = getattr(predict_last, 'mlmodels', None)
        self.assertEqual('semisupervisedSpectralClustering', mlmodel)
    
    # update one param and see if the underlying data get updated
    def test_param_fillin_1(self):
        # select unsupervised kmeans
        select = Select(self.selenium.find_element_by_id('id_predict_form-mlmodels'))
        select.select_by_index(0)
        # update param
        self.selenium.find_element_by_id('rNum').clear()
        self.selenium.find_element_by_id('rNum').send_keys('60')
        predict_last = PredictInfo.objects.last()
        params_str = getattr(predict_last, "parameters")
        params_obj = json.loads(params_str)
        rNum = int(params_obj['rNum'])
        self.assertEqual(rNum, 60)

    # have k min > k max and see if there is error message
    def test_param_fillin_2(self):
        # select unsupervised kmeans
        select = Select(self.selenium.find_element_by_id('id_predict_form-mlmodels'))
        select.select_by_index(3)
        # update param
        self.selenium.find_element_by_id('k_min').clear()
        self.selenium.find_element_by_id('k_min').send_keys('4')
        err_msg = self.selenium.find_element_by_css_selector("#k_min + .invalid_msg")
        err_msg_html = err_msg.get_attribute('innerHTML')
        self.assertNotEqual("", err_msg_html)