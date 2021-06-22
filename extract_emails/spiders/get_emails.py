import datetime
import json
import os
import pandas as pd
import pymongo
import PyPDF2
import re
import requests
import scrapy
import time
from io import StringIO
from scrapy.http import JsonRequest
from scrapy.http import Request
from scrapy.selector import Selector
from bs4 import BeautifulSoup


class GetEmailsSpider(scrapy.Spider):
    REPORT_TITLE = ''
    name = 'get_emails'
    headers = {
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'x-client-data': 'CIi2yQEIo7bJAQjBtskBCKmdygEIjqzKAQiGtcoBCP68ygEI58jKAQi0y8oB',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9',
    }
    
    dom_detailer_api_key = '5SUT34180BBFG'
    custom_settings = {
        'FEEDS': {
            'get_emails.csv' : {
                'format': 'csv',
                'encoding': 'utf-8'
            }
        },
        'FEED_EXPORTERS': {
            'csv': 'scrapy.exporters.CsvItemExporter',
        },
    }

    def __init__(self, use_db='', prt="", report_title='', use_csv='', user="", *args, **kwargs):
        # self.logger.debug(f'use_db---------------------------------------------------------{use_db}')
        self.logger.debug(f'report_title---------------------------------------------------------{report_title}')
        self.logger.debug(f'use_csv---------------------------------------------------------{use_csv}')
        self.urls = []
        self.email_addresses = []
        self.REPORT_TITLE = report_title

        # PRODUCTION ENV DB
        # self.client = pymongo.MongoClient("mongodb+srv://nayeem:imunbd990@cluster0.vh1iq.mongodb.net/bloggerhit?retryWrites=true&w=majority")
        self.client = pymongo.MongoClient("mongodb+srv://admin-santhej:2&fX#zF9JzG$@cluster0.3dv1a.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.db = self.client[str(user)]
        self.db[str(prt)]

        collections = self.db[str(prt)]
        allrawdata = collections.find({})
        xx = []
        for i in allrawdata:
            xx.append(i)
        print()

        new_data = []
        for j in xx:
            j.pop('_id')
            new_data.append(j)
        print(new_data[:10], len(new_data))


        # use_db will be true when user uploads a CSV file while running this spider
        # or choose to run both the spiders together
        if use_db == 'true':
            print()
            print("HERE ")
            print()
            if use_csv == 'true':
                self.logger.debug('DEBUG: Looking for user uploaded URLs in DB')
                url_data = self.db.uploadedcsvs.find({}, {'_id': 0, 'website_url': 1})
                self.logger.debug(f'URLs uploaded by user in CSV found')
            else:
                self.logger.debug('DEBUG: Looking for URLs in DB')
                url_data = self.db.urls.find({'report_title': report_title}, {'_id': 0, 'website_url': 1})
                self.logger.debug(f'URLs found for filter - report_title: {report_title}')
            for data in url_data:
                self.urls.append(
                    {
                        'url': data['website_url'].strip(),
                        'category': report_title.strip(),
                        'report_title': report_title.strip()
                    }
                )
        else:
            print("ELSE ________________________")
            # Read the CSV file & fillup the self.urls list
            # csv_data = pd.read_csv('guestpostscraper.out.csv')
            csv_data = new_data
            # print("Getting guestpostscraper -----------------------------------")
            for website_url, category, user in csv_data[['website_url', 'category', 'user']].values:
                self.urls.append(
                    {
                        'url': website_url.strip(),
                        'category': category.strip(),
                        'report_title': report_title.strip(),
                        'user': user.strip()
                    }
                )

        # print()
        # print()
        print("Self urls ----------------------self urls -------------------------", len(self.urls), self.urls)
        # print()
        # print()


        # Open an HTTP session for google.com and set cookies
        self.session = requests.Session()
        self.session.get('https://www.google.com/search', headers=self.headers)
        self.cookie = self._get_cookie()
        self.headers.update({'cookie': self.cookie})

        # we are going to limit the use of snov io access for limiting the cost
        self.snovio_access_token = self._get_snovio_access_token()
        if not self.snovio_access_token:
            self.logger.debug("ERROR: SNOVIO Access Token is not available. SNOVIO requests will be skipped.")

    def _get_cookie(self):
        cookies = []
        for key, value in self.session.cookies.get_dict().items():
            cookies.append('%s=%s' % (key, value))
        cookie = "; ".join(cookies)
        self.logger.debug('[INFO]  Cookie: %s -----------------------------------------------' % cookie)
        return cookie


    def _get_snovio_access_token(self):
        data = {
            "grant_type":"client_credentials",
            "client_id":"97fc7cadbba633d0c17a833e6dfccaff",
            "client_secret":"0eed64cb98e69a1735179fcee427a6cc"
        }
        response = requests.post('https://api.snov.io/v1/oauth/access_token', json=data)
        access_token = None
        if response.status_code == 200:
            print("--------------------------snov io --------------------------- succeed")
            access_token = response.json().get('access_token')

        self.logger.debug(f"DEBUG: SnovIO Access Token - {access_token}")
        return access_token
    

    def start_requests(self):
        # Access each URL in the self.urls list
        for url in self.urls:
            print("CHECkING - ", url['url'])

            if self.is_db_data_outdated(url['url']):
                domain = url['url'].split('/')[2].replace('www.', '')
                yield Request(
                    url['url'],
                    callback=self.parse,
                    headers=self.headers,
                    meta={
                        # 'dont_proxy': True,
                        'domain': domain,
                        'category': url['category'],
                        'report_title': url['report_title'],
                        'user': url['user']
                    }
                )

            # Check if the current url is last of the list
            # If yes then close the DB connection.
            if (len(self.urls) - 1) == self.urls.index(url):
                self.logger.debug('DEBUG: Last URL of the list. Closing DB connection.')
                self.client.close()
                print("------------------connection closed---------------------")


    def is_db_data_outdated(self, url):
        # data = self.db.emails.find_one({"url": url}, {'_id': 0, 'date': 1})
        data = self.db.get_email.find_one({"url": url}, {'_id': 0, 'date': 1})
        if data:
            today = datetime.datetime.today()
            db_date = datetime.datetime.strptime(data['date'], "%Y-%m-%d")
            delta = today - db_date
            self.logger.debug(f'DEBUG: Db data is ------------------------------------------------ {delta.days} days old')
            if delta.days > 30:
                self.logger.debug(f'DEBUG: Re-fetching from data web ------------------------------------------------')
                return True
            else:
                self.logger.debug(f'DEBUG: Skipping ------------------------------------------------ data fetch from web')
                return False
        else:
            self.logger.debug(f'DEBUG: No data found in db. ------------------------------------------------ Fetching from web')
            return True






    # parse callback funtion for working with response callback
    def parse(self, response):
        try:
            body = response.text
        except:
            if response.body:
                body = response.body.decode("utf-8", errors="ignore")
                if body.startswith('%PDF'):
                    body = self._read_pdf(response.body)

        # Parse website reponse
        self.email_addresses = []
        domain = response.meta['domain']

        # Find email addresses of the form user@domain.root
        if re.search(r"[a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # print('FOUND EMAIL 1', email)
            # self._filter_emails(emails)
            self._filter_emails(email)

        # Find email addresses of the form user<SPACES>@<SPACES>domain.root
        if re.search(r"[a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # self._filter_emails(emails)
            # print('FOUND EMAIL 2', email)
            self._filter_emails(email)

        # Find email addresses of the form user [at] domain [dot] root
        if re.search(r'\[at\].*\[dot\]', body):
            resp = re.sub(r'\s+\[at\]\s+', '@', body)
            resp = re.sub(r'\s+\[dot\]\s+', '.', resp)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)
            # print('FOUND EMAIL 3', email)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))

        # Find email addresses of the form user (at) domain (dot) root
        if re.search(r'\(at\).*dot', body, re.I):
            resp = re.sub(r'\s+\(at\)\s+', '@', body)
            resp = re.sub(r'\s+DOT\s+', '.', resp, re.I)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)
            # print('FOUND EMAIL 4', email)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))



        # here is the google and conditional block
        # here is the google and conditional block
        if self.email_addresses:
            # If email addresses are found then yield URL & email addresses
            unique_emails = list(dict.fromkeys([x.lower() for x in self.email_addresses]))



            print("-----------------------------------------got emails in first site----------------------------- ", self.email_addresses, response.url, unique_emails)
            self.email_addresses = []
            yield Request(
                f'http://domdetailer.com/api/checkDomain.php?domain={domain}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
                headers=self.headers,
                callback=self.parse_dom_details,
                meta={
                    # 'dont_proxy': True,
                    'url': response.url,
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'],
                    # response.meta['domain']
                    'user': response.meta['user'],
                    'domain': domain,   
                    'email': unique_emails[0] if unique_emails else 'NA',
                }
            )

        else:
            # Else access the URL and check if encoded emails are present.
            # If encoded emails found then decode the emails and yield
            yield Request(
                response.url,
                headers=self.headers,
                callback=self.parse_encoded_email,
                dont_filter=True,
                meta={
                    # 'dont_proxy': True,
                    'url': response.url,
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'],
                    # response.meta['domain']
                    'domain': domain,
                    'user': response.meta['user'],
                }
            )

            # If encoded emails are not found then search for emails in google and yield found emails
            # Search query example - site:techristic.com "@techristic.com" contact us
            if not self.email_addresses:
                domain = response.url.split('/')[2].replace('www.', '')
                u = response.url
                # url = f'https://www.google.com/search?q=site%3A{domain}+%22%40{domain}%22+contact+us&rlz=1C1GCEA_enIN901IN901&oq=site%3A{domain}+%22%40{domain}%22+contact+us&aqs=chrome..69i57j69i58.4168j0j7&sourceid=chrome&ie=UTF-8'
                url = f'https://www.google.com/search?q={domain}+email'
                headers = self.headers.copy()
                headers.update({'authority': 'www.google.com', 'X-Crawlera-Max-Retries': 0})
                # print("Checking GOOGLE --------------------------------", url)

                yield Request(
                    url,
                    headers=headers,
                    callback=self.parse_google_search,
                    dont_filter=True,
                    meta={
                        'url': response.url,
                        'category': response.meta['category'],
                        'report_title': response.meta['report_title'],
                        # response.meta['domain']
                        'domain': domain,
                        'user': response.meta['user'],
                    }
                )

            # print("After google search =================>>>>>>>>>>>>>", self.email_addresses)


            if not self.email_addresses:
                domain = response.url.split('/')[2]
                d = response.url.split('/')
                d1 = d[0]
                url = d1+"//"+domain
                # print("Checking Main  Website --------------------------------", url)
                url = url
                headers = self.headers.copy()
                headers.update({'authority': 'www.google.com', 'X-Crawlera-Max-Retries': 0})
                yield Request(
                    url,
                    headers=headers,
                    callback=self.parse_website_itself,
                    dont_filter=True,
                    meta={
                        # 'dont_proxy': True,
                        'url': response.url,
                        'category': response.meta['category'],
                        'report_title': response.meta['report_title'],
                        'domain': domain,
                        'user': response.meta['user'],
                    }
                )



            # snov io api key for getting email
            if not self.email_addresses:
                domain = response.url.split('/')[2].replace('www.', '')
                # Query snovio API for 100 email records of all type
                params = {
                    "domain": domain,
                    "type": "all",
                    "offset": 0,
                    "limit": 100
                }
                if self.snovio_access_token:
                    yield JsonRequest(
                        'https://api.snov.io/v1/get-domain-emails-with-info',
                        method='POST',
                        headers={'Authorization': f'Bearer {self.snovio_access_token}'},
                        data=params,
                        callback=self.parse_snovio_response,
                        dont_filter=True,
                        meta={
                            'url': response.url,
                            'category': response.meta['category'],
                            'report_title': response.meta['report_title'],
                            'domain': domain,
                            'user': response.meta['user'],
                        }
                    )
        


    def _filter_emails(self, email):
        # Extension to be ignored. If extracted email address contains any of these then ignore it
        exts_to_ignore = ['.jpg', '.jpeg', '.png', '.gif', 'tiff', '.psd', '.pdf', '.eps', '.webpack']
        # print("------------------inside filter---------------------", email)
        for ext in exts_to_ignore:
            if email.endswith(ext):
                break
        else:
            (user, domain) = email.split('@')
            # print("-----------------deep into filter--------------------", email)
            # Check if domain part of the extracted email is not like user@domain eg - a@b
            # Check if root domain of the email domain is not a number eg css@1.2.4
            if len(domain.split('.')) > 1 and not re.match(r'\d+', domain.split('.')[-1]):
                # Check the email string does not start with @ eg- @twitterhandle
                if not email.startswith('@'):
                    email = email.strip('-').strip('.')
                    email = re.sub(r'\s+|\[|\]', '', email)
                    self.email_addresses.append(email)
    

    # Method to parse encoded email addresses
    # Emails will have a class of __cf_email__.
    # Modify this method if you find any other xpath or css
    def parse_encoded_email(self, response):
        encoded_emails = []
        try:
            body = response.text
        except:
            if response.body:
                body = response.body.decode("utf-8", errors="ignore")
        resp = Selector(text=body)
        
        if resp.xpath('//span[@class="__cf_email__"]/@data-cfemail'):
            encoded_emails = resp.xpath('//span[@class="__cf_email__"]/@data-cfemail').getall()

        if encoded_emails:
            for encoded_email in encoded_emails:
                if encoded_email:
                    decoded_email = ""
                    k = int(encoded_email[:2], 16)
                    for i in range(2, len(encoded_email)-1, 2):
                        decoded_email += chr(int(encoded_email[i:i+2], 16) ^ k)

                    if decoded_email and not decoded_email.startswith('@'):
                        (user, domain) = decoded_email.split('@')
                        if len(domain.split('.')) != 1 and not re.match(r'\d+', domain.split('.')[-1]):
                            decoded_email = decoded_email.strip('-').strip('.')
                            decoded_email = re.sub(r'\s+|\[|\]', '', decoded_email)
                            self.email_addresses.append(decoded_email)
                    else:
                        self.logger.debug(f'ERROR: Decoded Email not found - {response.url}')

            print("-----------------------------------------got encoded emails----------------------------- ", self.email_addresses, response.url)
            unique_emails = list(dict.fromkeys([x.lower() for x in self.email_addresses]))
            yield Request(
                f'http://domdetailer.com/api/checkDomain.php?domain={response.meta["domain"]}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
                headers=self.headers,
                callback=self.parse_dom_details,
                meta={
                    # 'dont_proxy': True,
                    'url': response.meta['url'],
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'].replace(',', ' & '),
                    'domain': response.meta['domain'],
                    'email': unique_emails[0] if unique_emails else 'NA',
                }
            )
        else:
            self.email_addresses = []


    def parse_website_itself(self, response):
        email_addresses = []
        domain = response.meta['domain']
        try:
            body = response.text
        except:
            if response.body:
                body = response.body.decode("utf-8", errors="ignore")
            else:
                body = '<html></html>'
        # resp = Selector(text=body)

        # Find email addresses of the form user@domain.root
        if re.search(r"[a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # print('FOUND EMAIL 1', email)
            self._filter_emails(email)

        # Find email addresses of the form user<SPACES>@<SPACES>domain.root
        if re.search(r"[a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # self._filter_emails(emails)
            self._filter_emails(email)

        # Find email addresses of the form user [at] domain [dot] root
        if re.search(r'\[at\].*\[dot\]', body):
            resp = re.sub(r'\s+\[at\]\s+', '@', body)
            resp = re.sub(r'\s+\[dot\]\s+', '.', resp)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))

        # Find email addresses of the form user (at) domain (dot) root
        if re.search(r'\(at\).*dot', body, re.I):
            resp = re.sub(r'\s+\(at\)\s+', '@', body)
            resp = re.sub(r'\s+DOT\s+', '.', resp, re.I)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))
        # print("HERE WEBSITE :", self.email_addresses)
        if self.email_addresses:
            print("__________________________________________________Got email inside actual website___________________________________", self.email_addresses, response.url )
            unique_emails = list(dict.fromkeys([x.lower() for x in self.email_addresses]))
            yield Request(
                f'http://domdetailer.com/api/checkDomain.php?domain={response.meta["domain"]}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
                headers=self.headers,
                callback=self.parse_dom_details,
                meta={
                    # 'dont_proxy': True,
                    'url': response.url,
                    'user': response.meta['user'],
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'].replace(',', ' & '),
                    'domain': response.meta['domain'],
                    'email': unique_emails[0] if unique_emails else 'NA',
                }
            )
        else:
            self.email_addresses = []
            # "submit","Submit","SUBMIT","contactsales","ContactSales","CONTACTSALES","CONTACT-SALES", "contact-sales", "Contact-Sales","Contact-sales","contact-Sales","Contactsales","contactSales", "Quote","quote","QUOTE", "get-a-quote","Get-a-quote","quotes","Quotes","QUOTES"
            sample = [ "contact","Contact","CONTACT", "contactus","ContactUs","Contactus","contactUs","CONTACTUS","contact-us","Contact-us","Contact-Us","contact-Us","CONTACT-US"]
            soup = BeautifulSoup(body, 'html.parser') 
            alinks = []
            targetlinks = []
            for link in soup.find_all('a'):
                if link.get('href') not in alinks:
                    alinks.append(link.get('href'))

            # print("Alinks ------------------>>>> ",alinks)
            for j in range(len(alinks)):
                for samp in sample:
                    if str(samp) in str(alinks[j]):
                        temp = response.url
                        temp1 = alinks[j]
                        if temp in temp1:
                            if temp1 not in targetlinks:
                                targetlinks.append(temp1)
                        elif "https" in temp1:
                            if temp1 not in targetlinks:
                                targetlinks.append(temp1)
                        elif "http" in temp1:
                            if temp1 not in targetlinks:
                                targetlinks.append(temp1)
                        elif temp[-1] == "/" and temp1[0] == "/":
                            l = temp[:-1]+temp1
                            if l not in targetlinks:
                                targetlinks.append(l)
                        elif temp[-1] != "/" and temp1[0] != "/":
                            l = temp+"/"+temp1
                            if l not in targetlinks:
                                targetlinks.append(l)
                        else:
                            l = temp+temp1
                            if l not in targetlinks:
                                targetlinks.append(l)


            print("Target links ------------------>>>> ",targetlinks)

            for tar in targetlinks:
                yield Request(
                url = tar,
                headers=self.headers,
                callback=self.parse_contact_page,
                meta={
                    # 'dont_proxy': True,
                    'url': tar,
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'],
                    'domain': domain,
                    'user': response.meta['user'],

                }
            )
        



    def parse_dom_details(self, response):
        if response.headers.get('Content-Type'):
            try: 
                json_data = json.loads(response.text)
            except:
                json_data = {}
        else:
            json_data = {}
    
        yield {
            'website': response.meta['domain'],
            'url': response.meta['url'],
            'category': response.meta['category'],
            'report_title': response.meta['report_title'].replace(',', ' & '),
            'user': response.meta['user'],
            'email': response.meta['email'],
            'da': json_data['mozDA'] if 'mozDA' in json_data else 'NA',
            'pa': json_data['mozPA'] if 'mozPA' in json_data else 'NA',
            'cf': json_data['majesticCF'] if 'majesticCF' in json_data else 'NA',
            'tf': json_data['majesticTF'] if 'majesticTF' in json_data else 'NA',
            'date': datetime.datetime.now().strftime("%Y-%m-%d"),
            # 'snov_io': response.meta.get('snov_io') or 'No'
        }


    def parse_contact_page(self, response):
        email_addresses = []
        domain = response.meta['domain']
        try:
            body = response.text
        except:
            if response.body:
                body = response.body.decode("utf-8", errors="ignore")
            else:
                body = '<html></html>'

        # Find email addresses of the form user@domain.root
        if re.search(r"[a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # print('FOUND EMAIL 1', email)
            self._filter_emails(email)

        # Find email addresses of the form user<SPACES>@<SPACES>domain.root
        if re.search(r"[a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # self._filter_emails(emails)
            self._filter_emails(email)

        # Find email addresses of the form user [at] domain [dot] root
        if re.search(r'\[at\].*\[dot\]', body):
            resp = re.sub(r'\s+\[at\]\s+', '@', body)
            resp = re.sub(r'\s+\[dot\]\s+', '.', resp)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))

        # Find email addresses of the form user (at) domain (dot) root
        if re.search(r'\(at\).*dot', body, re.I):
            resp = re.sub(r'\s+\(at\)\s+', '@', body)
            resp = re.sub(r'\s+DOT\s+', '.', resp, re.I)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))


        if self.email_addresses:
            print("__________________________________________________Got email in contact page ___________________________________", self.email_addresses, response.url)
            unique_emails = list(dict.fromkeys([x.lower() for x in self.email_addresses]))
            # print("UNIQUE EMAILS IN GOOGLE SEARCH ", unique_emails)
            yield Request(
                f'http://domdetailer.com/api/checkDomain.php?domain={response.meta["domain"]}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
                headers=self.headers,
                callback=self.parse_dom_details,
                meta={
                    # 'dont_proxy': True,
                    'url': response.url,
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'].replace(',', ' & '),
                    'domain': response.meta['domain'],
                    'email': unique_emails[0] if unique_emails else 'NA',
                    'user': response.meta['user'],
                }
            )
        else:
            self.email_addresses = []


   
    # Method to parse google search results
    # Each google search results will be stored under a span of class "st"
    # Modify this method to enhance google search results.
    def parse_google_search(self, response):
        email_addresses = []
        # domain = response.meta['url'].split('/')[2].replace('www.', '')
        domain = response.meta['domain']
        try:
            body = response.text
        except:
            if response.body:
                body = response.body.decode("utf-8", errors="ignore")
            else:
                body = '<html></html>'
        # resp = Selector(text=body)

        # print()
        # print()
        # # print("BODY OF DOMANI:", domain, body)
        # print()
        # print()

        # Find email addresses of the form user@domain.root
        if re.search(r"[a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # print('FOUND EMAIL 1', email)
            self._filter_emails(email)

        # Find email addresses of the form user<SPACES>@<SPACES>domain.root
        if re.search(r"[a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+", body):
            email = re.search(r"([a-z0-9\.\-+_]+\s+?\@\s+?[a-z0-9\.\-+_]+\.[a-z]+)", body).group(1)
            # self._filter_emails(emails)
            self._filter_emails(email)

        # Find email addresses of the form user [at] domain [dot] root
        if re.search(r'\[at\].*\[dot\]', body):
            resp = re.sub(r'\s+\[at\]\s+', '@', body)
            resp = re.sub(r'\s+\[dot\]\s+', '.', resp)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))

        # Find email addresses of the form user (at) domain (dot) root
        if re.search(r'\(at\).*dot', body, re.I):
            resp = re.sub(r'\s+\(at\)\s+', '@', body)
            resp = re.sub(r'\s+DOT\s+', '.', resp, re.I)
            email = re.search(r"([a-z0-9\.\-+_]+\@[a-z0-9\.\-+_]+\.[a-z]+)", body)

            # self._filter_emails(emails)
            if email:
                self._filter_emails(email.group(1))

        # print("HERE GOOGLE", self.email_addresses)

        if self.email_addresses:
            print("__________________________________________________Got email in GOOGLE SEARCH ___________________________________", self.email_addresses, response.url)
            unique_emails = list(dict.fromkeys([x.lower() for x in self.email_addresses]))
            # print("UNIQUE EMAILS IN GOOGLE SEARCH ", unique_emails)
            yield Request(
                f'http://domdetailer.com/api/checkDomain.php?domain={response.meta["domain"]}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
                headers=self.headers,
                callback=self.parse_dom_details,
                meta={
                    # 'dont_proxy': True,
                    'url': response.meta['url'],
                    'category': response.meta['category'],
                    'report_title': response.meta['report_title'].replace(',', ' & '),
                    'domain': response.meta['domain'],
                    'email': unique_emails[0] if unique_emails else 'NA',
                    'user': response.meta['user'],

                }
            )
        else:
            self.email_addresses = []



    # Method to parse SNOVIO API response
    # API query is sent to search for all type of emails ie: personal + generic
    # First item from each list is picked and joined as a string
    def parse_snovio_response(self, response):
        self.email_addresses = []
        if response.status == 200:
            json_data = response.json()
            self.logger.debug('DEBUG: SNOVIO API Response')
            self.logger.debug(json_data)
            if json_data['result']:
                personal_emails = [x for x in json_data['emails'] if "firstName" in x]
                generic_emails = [x for x in json_data['emails'] if "firstName" not in x]
                if personal_emails:
                    self.email_addresses.append(personal_emails[0].get('email'))
                if generic_emails:
                    self.email_addresses.append(generic_emails[0].get('email'))

        yield Request(
            f'http://domdetailer.com/api/checkDomain.php?domain={response.meta["domain"]}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
            headers=self.headers,
            callback=self.parse_dom_details,
            meta={
                'dont_proxy': True,
                'url': response.meta['url'],
                'category': response.meta['category'],
                'report_title': response.meta['report_title'].replace(',', ' & '),
                'user': response.meta['user'],
                'domain': response.meta['domain'],
                'email': ','.join(self.email_addresses) if self.email_addresses else 'NA',
                'snov_io': 'Yes'
            }
        )
    
    def _read_pdf(self, response_body):
        body = ""
        # body = response.body.decode("utf-8", errors="ignore")
        with open('response.pdf', 'wb') as file:
            file.write(response_body)
        # creating a pdf file object
        pdfFileObj = open('response.pdf', 'rb')
        # creating a pdf reader object
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        # Go through all the pages and extract text
        for page_num in range(pdfReader.numPages):
            # creating a page object
            pageObj = pdfReader.getPage(page_num)
            # extracting text from page
            body += pageObj.extractText()
        return body










































































































# #########################################################################################################################################################
# #########################################################################################################################################################
# #########################################################################################################################################################
# #########################################################################################################################################################

    # Method to parse SNOVIO API response
    # API query is sent to search for all type of emails ie: personal + generic
    # Personal & Generic emails are filtered and stored in two lists
    # First item from each list is picked and joined as a string
    # def parse_snovio_response(self, response):
    #     email_addresses = []
    #     if response.status == 200:
    #         json_data = response.json()
    #         self.logger.debug('DEBUG: SNOVIO API Response')
    #         self.logger.debug(json_data)
    #         if json_data['result']:
    #             personal_emails = [x for x in json_data['emails'] if "firstName" in x]
    #             generic_emails = [x for x in json_data['emails'] if "firstName" not in x]
    #             if personal_emails:
    #                 email_addresses.append(personal_emails[0].get('email'))
    #             if generic_emails:
    #                 email_addresses.append(generic_emails[0].get('email'))

    #     yield Request(
    #         f'http://domdetailer.com/api/checkDomain.php?domain={response.meta["domain"]}&app=DomDetailer&apikey={self.dom_detailer_api_key}&majesticChoice=root',
    #         headers=self.headers,
    #         callback=self.parse_dom_details,
    #         meta={
    #             'dont_proxy': True,
    #             'url': response.meta['url'],
    #             'category': response.meta['category'],
    #             'report_title': response.meta['report_title'].replace(',', ' & '),
    #             'domain': response.meta['domain'],
    #             'email': ','.join(email_addresses) if email_addresses else 'NA',
    #             'snov_io': 'Yes'
    #         }
    #     )

    # def _filter_emails(self, emails):
    #     for email in emails:
    #         # Check if '.png' not in email
    #         if email.endswith('.jpg'):
    #             continue
    #         # Check if '.jpg' not in email
    #         if email.endswith('.png'):
    #             continue
    #         # Check 'gif' not in email:
    #         if email.endswith('.gif'):
    #             continue
    #         (user, domain) = email.split('@')
    #         # Check if domain part of the extracted email is not like user@domain eg - a@b
    #         # Check if root domain of the email domain is not a number eg css@1.2.4
    #         if len(domain.split('.')) > 1 and not re.match(r'\d+', domain.split('.')[-1]):
    #             # Check the email string does not start with @ eg- @twitterhandle
    #             if not email.startswith('@'):
    #                 email = email.strip('-').strip('.')
    #                 email = re.sub(r'\s+|\[|\]', '', email)
    #                 self.email_addresses.append(email)


    # def _filter_emails(self, email):
    #     # Extension to be ignored. If extracted email address contains any of these then ignore it
    #     exts_to_ignore = ['.jpg', '.jpeg', '.png', '.gif', 'tiff', '.psd', '.pdf', '.eps', '.webpack']
    #     for ext in exts_to_ignore:
    #         if email.endswith(ext):
    #             break
    #     else:
    #         (user, domain) = email.split('@')
    #         # Check if domain part of the extracted email is not like user@domain eg - a@b
    #         # Check if root domain of the email domain is not a number eg css@1.2.4
    #         if len(domain.split('.')) > 1 and not re.match(r'\d+', domain.split('.')[-1]):
    #             # Check the email string does not start with @ eg- @twitterhandle
    #             if not email.startswith('@'):
    #                 email = email.strip('-').strip('.')
    #                 email = re.sub(r'\s+|\[|\]', '', email)
    #                 self.email_addresses.append(email)
    
    # def _read_pdf(self, response_body):
    #     body = ""
    #     # body = response.body.decode("utf-8", errors="ignore")
    #     with open('response.pdf', 'wb') as file:
    #         file.write(response_body)
    #     # creating a pdf file object
    #     pdfFileObj = open('response.pdf', 'rb')
    #     # creating a pdf reader object
    #     pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    #     # Go through all the pages and extract text
    #     for page_num in range(pdfReader.numPages):
    #         # creating a page object
    #         pageObj = pdfReader.getPage(page_num)
    #         # extracting text from page
    #         body += pageObj.extractText()
    #     return body