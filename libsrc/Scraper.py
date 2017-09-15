"""Scraper"""

import sys
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

class GradeScraper:
    """Scraper for UTM students grades"""

    def __init__(self, username, password):
        self.enrollment = username

        self.username = 'al0' + self.enrollment
        self.banneruser = 'T0' + self.enrollment
        self.useremail = self.username + "@tecmilenio.mx"

        self.password = password

        self.base_urls = {
            # This URL is used to get to the real login page using their API. See
            # get_utm_url()
            'OFFICE365': 'https://login.microsoftonline.com/common/userrealm',
            # This URL is accessed once the program is logged into the site
            # (SharePoint) to generate Banner cookies. See login_and_get_cookies()
            'BANNER': 'https://beis.tecmilenio.mx:7007/ssomanager/saml/login?relayState=/c/auth/SSB?pkg=bwskflib.P_SelDefTerm%3Fterm_in%3D%26calling_proc_name%3Dbwzkacrp.p_DispGradesAttStu',
            # Term Selection URL, contains available terms. GET, needs cookies. See
            # get_available_terms()
            'BANNERTERM': 'https://ssbutm.tecmilenio.mx/BTMPROD/bwskflib.P_SelDefTerm?term_in=&calling_proc_name=bwzkacrp.p_DispGradesAttStu',
            # Grades URL, contains current averages. POST, needs cookies and term_in,
            # the term to get grades from. See get_grades()
            'BANNERGRADES': 'https://ssbutm.tecmilenio.mx/BTMPROD/bwzkacrp.p_DispGradesAttStu',
            'BANNERBASE': 'https://ssbutm.tecmilenio.mx'
        }

        self.currentcookies = self.login_and_get_cookies()
    # HTTP Requests

    def get_utm_url(self):
        """Gets UTM login URL from Microsoft Office 365 login"""
        parameters = {
            'user': self.useremail,
            'api-version': '2.1',
            # stsRequests makes the log in site to redirect us to SharePoint/MiPortal
            # Not using this will get us to Outlook and not MiPortal
            'stsRequest': 'rQIIAdNiNtQztFIxgABjXRCpa5CWZqibnApiIYEiIS6BuR8bT9xwYHB4POmh-PVndhdWMRpmlJQUFFvp65eW5KamlOoVZyQWpRbkZ-aV6CXn5-rHp-UX5Rbrp6SmJZbmlOglFhdU7GBkvMDI-IKRcRVToZOBo4Gpm7mZm4ujpauTm6mJuYGribmjmbmBs6OTgZGZhaOjobGLqbmFE1Dc0tRUF6jQ0NLczdnMydnc2MDS3MDJ1cTJ3NLA1dXYzdnF1cXAHEgau5q6ugGVGTk7G5qYulgamxs4mpuaupqZG99i4vd3LC3JMAIR-UWZVamfmDhBbowvyC8umcXMaLCJWcXA2CDV0tQwRdcsNS1F18QozVTXwsTIXDcpMcnM2Cg5zcLA0OAUM1t-QWpeZsoFFsZXLDwGzFYcHFwCDBIMCgw_WBgXsQIDS8z-XuvOKy3umx9L-G8pU2E4xarvGOroGpilrZ9X7ppfbp4RYBri5O5YnhjmW2SubZlokOLnn5VdVlqW5B0eaWtqZTiBjXECG9suTtIDGQA1',
            'checkForMicrosoftAccount': 'true'
        }
        response = requests.get(self.base_urls['OFFICE365'], params=parameters)
        data = response.json()
        return data['AuthURL']

    def get_available_terms_site(self, cookies):
        """Returns the HTML site of available terms with codes and labels"""
        terms_response = requests.get(
            self.base_urls['BANNERTERM'], cookies=cookies)
        return terms_response.text

    def get_grades_site(self, cookies, term):
        """Returns the HTML grades site for the current term and user (cookies)."""
        payload = {
            'term_in': term
        }
        grades_response = requests.post(
            self.base_urls['BANNERGRADES'], cookies=cookies, data=payload)
        return grades_response.text

    def get_subject_page(self, cookies, url):
        """Returns the HTML site of the grades OR absences of the subject provided"""
        subject_grade_response = requests.get(url, cookies=cookies)
        return subject_grade_response.text

    # Login
    def login_and_get_cookies(self):
        """Logs in to the site and gets the necessary cookies to scrape Banner with HTTP APIs
            NOTE: Lots of redirections and JavaScript when doing this (SAML too)
            NOTE: This is the slowest method in this program (usually 5-20 seconds per user) due to the whole browser simulation/execution
        """
        service_args = [
            '--load-images=false'
        ]
        driver = webdriver.PhantomJS(service_args=service_args)
        driver.get(self.get_utm_url())

        password = driver.find_element_by_id("PasswordTextBox")
        password.send_keys(self.password)

        driver.find_element_by_name(
            "ctl00$ContentPlaceHolder1$SubmitButton").click()

        driver.get(self.base_urls['BANNER'])
        element = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.ID, "helpWindow")))

        if 'Registration' in driver.title:
            cookies = driver.get_cookies()

        cookies_dict = {}

        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']

        driver.quit()
        return cookies_dict

    # Methods that return data structures
    def get_available_terms(self, terms_page):
        """Returns a dictionary of available terms with codes and labels"""
        terms_page = BeautifulSoup(terms_page, 'lxml')
        terms_dict = {}
        for option in terms_page.find_all("option"):
            termid = option['value']
            termlabel = option.text.rstrip('\n')
            terms_dict[termid] = termlabel
        return terms_dict

    def get_grades(self, grades_page):
        """Parses the grades website and returns a list of lists"""
        soup = BeautifulSoup(grades_page, 'lxml')

        data = []

        table = soup.find('table', {'class': 'dataentrytable'})

        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [element.text.strip() for element in cols]
            data.append(
                [element for element in cols if element not in ['Extension', '']])
        return data

    def get_student_info(self, grades_page):
        """Obtain name, program, level and campus of the current student as a dictionary"""
        soup = BeautifulSoup(grades_page, 'lxml')

        staticheaders = soup.find('div', {'class': 'staticheaders'})
        studentfullname = staticheaders.contents[0].replace(
            self.banneruser, '').strip()

        student_info_table = soup.find('table', {'class': 'datadisplaytable'})
        student_info = []
        rows = student_info_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            student_info.append(cols[1].text.strip())

        info_dict = {
            'fullname': studentfullname,
            'program': student_info[0],
            'level': student_info[1],
            'campus': student_info[2]
        }

        return info_dict

    def get_subject_detail(self, grades_page):
        """Parses the grades website and returns a dictionary of dictionaries
            with the grades, absences and links to their details"""
        soup = BeautifulSoup(grades_page, 'lxml')

        data = {}

        table = soup.find('table', {'class': 'dataentrytable'})
        rows = table.find_all('tr')
        for row in rows[1::]:
            cols = row.find_all('td')
            a_element = cols[4].find('a')
            a_element_absence = cols[6].find('a')
            if a_element is not None:
                gradelink = self.base_urls['BANNERBASE'] + a_element['href']
                grade = cols[4].text.strip()
                detail = {
                    'grade': grade,
                    'gradelink': gradelink,
                    'absences': '0',
                    'absenceslink': ''
                }
                if a_element_absence is not None:
                    absenceslink = self.base_urls['BANNERBASE'] + \
                        a_element_absence['href']
                    absences = cols[6].text.strip()
                    detail['absences'] = absences
                    detail['absenceslink'] = absenceslink

                data[cols[2].text] = detail

        return data

    def get_subject_grade_detail(self, subject_grade_page):
        """Parses the subject grades website and returns a dictionary"""
        soup = BeautifulSoup(subject_grade_page, 'lxml')

        data = []

        table = soup.find_all('table', {'class': 'datadisplaytable'})[1]
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [element.text.strip() for element in cols]
            data.append([element for element in cols])
        return data

    # Methods that return things to be printed

    def averages_as_string_list(self, term, detailed=False):
        """Returns the averages of all the subjects found on term as a list"""
        grades_site = self.get_grades_site(self.currentcookies, term)

        grade_table = self.get_grades(grades_site)

        grade_table_string = []

        if detailed is not True:
            grade_table_string.append(
                "Materia\t\t\t\t\t\tPromedio\tFaltas")  # Prints basic info
        elif detailed is True:
            grade_table_string.append(
                "Materia\t\t\t\t\t\tPromedio\tFaltas\tCodigo\t\tGrupo\tLimite de Faltas")  # Prints all info

        for averagedata in grade_table[1::]:
            if detailed is not True:
                grade_table_string.append(
                    '{0}{1}\t\t{2}'.format(averagedata[2], averagedata[4], averagedata[6]))
            elif detailed is True:
                grade_table_string.append(
                    '{0}{1}\t\t{2}\t{3}\t{4}\t{5}'.format(averagedata[2].ljust(48), averagedata[4], averagedata[6], averagedata[1], averagedata[3], averagedata[5]))
        if detailed is True:
            student_info = self.get_student_info(grades_site)
            # Prints student info as part of the grades
            grade_table_string.insert(0, "{0} {1}\nPrograma: {2}\nNivel: {3}\tCampus: {4}\n".format(
                self.banneruser, student_info['fullname'], student_info['program'],
                student_info['level'], student_info['campus']))

        return grade_table_string

    def averages_as_string(self, term, detailed=False):
        """Returns the averages of all the subjects found on term as a fully formatted string"""
        string = ""
        for line in self.averages_as_string_list(term, detailed):
            string += line + "\n"

        return string

    def get_subject_details_as_string_list(self, term):
        """Prints each subject detail of grades"""
        grades_site = self.get_grades_site(self.currentcookies, term)
        subject_info = self.get_subject_detail(grades_site)
        string_list = []
        for key in subject_info:
            subject_page = self.get_subject_page(self.currentcookies, subject_info[key]['gradelink'])
            subject_data = self.get_subject_grade_detail(subject_page)
            string_list.append('\t\t' + key)
            string_list.append("\t{0}\t\t\t\t{1}".format('Actividad', 'Calificacion'))
            for data in subject_data[1::]:
                grade = data[4]
                if grade == '':
                    grade = 'Vacia'
                string_list.append("{0}\t{1}".format(data[0].capitalize().ljust(40), grade))
        return string_list

    def subject_details_as_string(self, term):
        """Returns the averages of all the subjects found on term as a fully formatted string"""
        string = ""
        for line in self.get_subject_details_as_string_list(term):
            string += line + "\n"
        #page = self.get_available_terms_site(self.currentcookies)
        #print(self.get_available_terms(page))
        return string
    def print_subject_full_detail(self, term):
        print("-" * 90)
        print(self.averages_as_string(term, True))
        print(self.subject_details_as_string(term))
        print("-" * 90)