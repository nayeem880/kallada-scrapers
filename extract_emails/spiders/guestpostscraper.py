# import datetime
import os
import scrapy
import tldextract
from scrapy.utils.project import get_project_settings
from scrapy.http import Request
from urllib.parse import quote, unquote
from scrapy.linkextractors import LinkExtractor



class GuestpostscraperSpider(scrapy.Spider):
    name = 'guestpostscraper'
    allowed_domains = ['google.com']
    start_urls = []
    scraped_urls = []
    count = 0
    domains_scraped = []
    queries = []
    REPORT_TITLE=''
    total = 0
    user = ''


    # guestpost_keywords = ['intitle:"write to us"',
    #                       'intitle:"connect with us"', 'intitle:"marketing"',
    #                       'intitle:"sales"', 'intitle:"customer support"']
    guestpost_keywords = ['intitle: "write for us"','intitle: "write for me"','intitle: "contribute to"',
                        'intitle: "submit"+inurl: blog','submit a guest post', 'inurl: /guest-post/',
                        '"guest post"','"guest post by"','"accepting guest posts"',
                        '"guest post guidelines"','"guest author"','"guest article"',
                        '"guest column"','"become a contributor"']
    guestpost_keywords_1 = ['"inpostauthor: guest"','inpostauthor: "guest blog"','inpostauthor: "guest post"']
    
    
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
                    
    write_for_us_url = ''
    custom_settings = {
        'FEEDS': {
            'guestpostscraper.csv' : {
                'format': 'csv',
                'encoding': 'utf-8'
            }
        },
        'FEED_EXPORTERS': {
            'csv': 'scrapy.exporters.CsvItemExporter',
        },
    }

    def __init__(self, seed_keywords="", report_title='', user="", *args, **kwargs):
        seed_keywords = seed_keywords.replace("[","")
        seed_keywords = seed_keywords.replace("]","")
        seed_keywords = seed_keywords.replace("'","")
        self.seed_keywords = seed_keywords.replace("_"," ")

        self.report_title = report_title
        print('---------------DEBUG: seed_keywords - %s' % self.seed_keywords)
        print('---------------DEBUG: type seed_keywords - %s' % type(self.seed_keywords))
        print('---------------DEBUG: report_title - %s' % self.report_title)
        print('---------------DEBUG: report_title type - %s' % type(self.report_title))
        self.REPORT_TITLE = self.report_title
        self.user = user
        # settings=get_project_settings()
        # print('-------------------------------------------settings -------------------------------------------', settings.get("DOWNLOAD_DELAY"))
        print("REPORT TITLE ++++++++++++++++ ", self.REPORT_TITLE, self.user)







    def start_requests(self):
        for seed_keyword in self.seed_keywords.split(','):
            self.write_for_us_url = 'https://www.google.com/search?q=' + quote(seed_keyword + ' intitle:"write for us"')
            print("write for us url------------------- ", self.write_for_us_url)

            for i in self.guestpost_keywords:
                tmp = seed_keyword + " " + i
                self.queries.append(tmp)

            for i in self.guestpost_keywords_1:
                tmp =  i + " " + seed_keyword
                self.queries.append(tmp)
            # unicode_query = generate_unicode_queries(queries)


        print("QUERIES -------------------------------------------------------- ", len(self.queries), self.queries)
        print()
        print()

        after_quote=[]
        for i in self.queries:
            i = quote(i)
            after_quote.append(i)
            i = 'https://www.google.com/search?q=' + i
            print("------------------------------------", i)
            if i not in self.start_urls:
                self.start_urls.append(i)
        # print("START URLS -------------------------------------------------------- ",  len(self.start_urls))




        num = 0
        for url in self.start_urls:
            final_final_each_seed = ''
            key_list = self.seed_keywords.split(',')
            for each_seed in key_list:
                # print("EACH ================= ", each_seed)
                each_seed_items = ''
                final_each_seed =  ''

                if " " in each_seed:
                    each_seed_items = each_seed.strip().split(" ")
                    final_each_seed = each_seed.strip().replace(" ", '_')
                elif "_" in each_seed:
                    each_seed_items = each_seed.strip().split("_")
                    final_each_seed = each_seed.strip()
                else:
                    each_seed_items = [each_seed.strip()]
                    final_each_seed = each_seed.strip()

                # print("EACH SEED ITEMS ---------------------- >>>>> ", each_seed_items, type(each_seed_items), final_each_seed)
                flag = ''

                for i in each_seed_items:
                    if i in url:
                        flag = True
                    else:
                        flag = False
                        break
                
                if flag == True:
                    final_final_each_seed = final_each_seed

            item = {
                'start_url': url,
                'category': final_final_each_seed,
                'report_title': self.report_title,
                'user': self.user
            }
            # print("EACH URL ---------------------->>>> ", item)
            num+=1
            self.total+=1
            request = Request(url, dont_filter=True)
            request.meta['item'] = item
            try:
                yield request
            except Exception as e:
                print(e)
        print("Initial url number ======================> ", num, len(self.start_urls))
        print()



                    

    def parse(self, response):
        try:
            # results = response.xpath('//*[@id="rso"]/div/div[*]/div/div/div[1]/a').extract()
            # results = response.xpath('//*[@id="rso"]/div/div[*]/div/div/div[*]/a/@href').getall()
            results = response.xpath('//*[@id="rso"]/div/div[*]/div/div[1]/a/@href').getall()
            

            next_page = response.xpath('//*[@id="pnnext"]/@href').extract()
            absolute_nextpageurl = ""

            # print("SCRAPED URLS----------------------------------->>>>>>>>", self.scraped_urls)
            print("Results ----------------------------------->>>>>>>>", results, len(results))
            print("Next page ----------------------------------->>>>>>>>", next_page)


            # self.scraped_urls = self.scraped_urls + results
            self.scraped_urls.append(results)
            # working with resutls
            # working with resutls
            # resu = list(results)
            for r in results:
                ext = tldextract.extract(r)
                # print("---------------------------extract tld",ext)
                
                if not (ext.domain in ['wordpress', 'pinterest'] or ext.suffix == 'it' or ext.domain in self.domains_scraped):
                    self.domains_scraped.append(ext.domain)
                    yield {
                        "website_url": r,
                        "base_url": response.meta['item']['start_url'],
                        "category": response.meta['item'].get('category') or 'None',
                        'report_title': response.meta['item'].get('report_title') or 'None',
                        'user': response.meta['item'].get('user') or 'None',
                    }


            if next_page != []:
                absolute_nextpageurl = "https://www.google.com" + next_page[0]
                # print("ABSOLUTE next page----------------------------------->>>>>>>>", absolute_nextpageurl)

                r = Request(absolute_nextpageurl, dont_filter=True)
                item = {
                    'start_url': response.meta['item']['start_url'],
                    'category': response.meta['item'].get('category') or 'None',
                    'report_title': response.meta['item'].get('report_title') or 'None',
                    'user': response.meta['item'].get('user') or 'None',

                }

                # print("-----------------------------------ITEM   222222 ", item)
                r.meta['item'] = item

                if response.meta['item']['start_url'] == self.write_for_us_url:
                    if "start=50" not in next_page[0]: # you can change start param here for the write for us URL
                        self.total+=1
                        yield r
                elif "start=50" not in next_page[0]: # This is for the rest of the urls
                    self.total+=1
                    yield r
            print("TOTAL WEBSITE VISITED ", self.total)
        except:
            print("Error - found", response, response.url)

