# import datetime
import os
import scrapy
import tldextract
from scrapy.utils.project import get_project_settings
from scrapy.http import Request
from urllib.parse import quote, unquote


class GuestpostscraperSpider(scrapy.Spider):
    name = 'guestpostscraper'
    allowed_domains = ['google.com']
    start_urls = []
    scraped_urls = []
    count = 0
    domains_scraped = []
    queries = []

  
    # guestpost_keywords = ['intitle:"write to us"',
    #                       'intitle:"connect with us"', 'intitle:"marketing"',
    #                       'intitle:"sales"', 'intitle:"customer support"']

    guestpost_keywords = ['intitle:"write for us"','intitle:"write for me"','intitle:"contribute to"',
                        'intitle:"submit"+inurl:blog','submit a guest post', 'inurl:/guest-post/',
                        '"guest post"','"guest post by"','"accepting guest posts"',
                        '"guest post guidelines"','"guest author"','"guest article"',
                        '"guest column"','"become a contributor"']

    guestpost_keywords_1 = ['"inpostauthor:guest"','inpostauthor:"guest blog"','inpostauthor:"guest post"']

                     



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

    def __init__(self, seed_keywords='', report_title='', *args, **kwargs):
        self.seed_keywords = seed_keywords
        self.report_title = report_title or self.seed_keywords
        self.report_title = self.report_title.replace(',', '_')
        print('--------------------------------------------------------DEBUG: seed_keywords - %s' % seed_keywords)
        print('--------------------------------------------------------DEBUG: report_title - %s' % report_title)

        settings=get_project_settings()
        # print('-------------------------------------------settings -------------------------------------------', settings.get("DOWNLOAD_DELAY"))






    def start_requests(self):
        for seed_keyword in self.seed_keywords.split(','):
            self.write_for_us_url = 'https://www.google.com/search?q=' + quote(seed_keyword + ' intitle:"write for us"')
            print()
            print("write for us url----------------------------write for us url---------------------------- write for us url", self.write_for_us_url)

            for i in self.guestpost_keywords:
                tmp = seed_keyword + " " + i
                self.queries.append(tmp)

            for i in self.guestpost_keywords_1:
                tmp =  i + " " + seed_keyword
                self.queries.append(tmp)
            # print()
            # print()
            # unicode_query = generate_unicode_queries(queries)


        print()
        print("QUERIES -------------------------------------------------------- ", self.queries)
        print()

        print("START URLS :", self.start_urls)
        for i in self.queries:
            i = quote(i)
            print("AFTER QUOTE ", i)
            i = 'https://www.google.com/search?q=' + i
            # print("------------------------------------", i)
            if i not in self.start_urls:
                self.start_urls.append(i)
        print()
        print("START URLS -------------------------------------------------------- ", self.start_urls, len(self.start_urls))
        print()


        for url in self.start_urls:
            rtitle = ''
            listt = self.seed_keywords.split(',')
            for each_seed in listt:
                if (len(listt) - 1) == listt.index(each_seed):
                    final_each_seed = each_seed.replace(" ", '_')
                
                else:
                    final_each_seed = each_seed.replace(" ", '_') + "_"

                rtitle = rtitle+final_each_seed


            for each_seed in self.seed_keywords.split(','):
                print("EACH SEED ", each_seed)
                final_each_seed = each_seed.replace(" ", '_')
                print("FINAL EACH SEED ", final_each_seed)
                each_seed_items = each_seed.split(" ")

                print()
                print(url)
                print("EACH ITEM OF each SEEDS ----------------------", each_seed_items)
                flag = ''

                for i in each_seed_items:
                    if i in url:
                        flag = True
                    else:
                        flag = False
                
                if flag == True:
                    item = {
                        'start_url': url,
                        # 'category': seed_keyword.strip().replace(' ', '_'),
                        'category': final_each_seed,
                        'report_title': rtitle,
                        # 'report_title': self.report_title
                    }

                    print("-----------------------------------ITEM ", item)
                    request = Request(url, dont_filter=True)

                    # set the meta['item'] to use the item in the next call back
                    request.meta['item'] = item
                    try:
                        yield request
                        print("----------------------------------------------------------------------", request)
                    except Exception as e:
                        print('---------------------- ERROR ----------------------')
                        print(e)





                








                    

    def parse(self, response):
        # results = response.xpath('//*[@id="rso"]/div/div[*]/div/div/div[1]/a').extract()
        results = response.xpath('//*[@id="rso"]/div/div[*]/div/div/div[1]/a/@href').getall()
        next_page = response.xpath('//*[@id="pnnext"]/@href').extract()
        absolute_nextpageurl = ""

        print()
        print()
        # print("SCRAPED URLS----------------------------------->>>>>>>>", self.scraped_urls)
        # print("Results ----------------------------------->>>>>>>>", results)
        # print("Next page ----------------------------------->>>>>>>>", next_page)

        print()
        print()


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
                    # 'report_title': self.report_title
                }


        if next_page != []:
            absolute_nextpageurl = "https://www.google.com" + next_page[0]
            # print("ABSOLUTE next page----------------------------------->>>>>>>>", absolute_nextpageurl)

            r = Request(absolute_nextpageurl, dont_filter=True)
            item = {
                'start_url': response.meta['item']['start_url'],
                'category': response.meta['item'].get('category') or 'None',
                'report_title': response.meta['item'].get('report_title') or 'None',
                # 'report_title': self.report_title
            }

            # print("-----------------------------------ITEM   222222 ", item)
            r.meta['item'] = item

            if response.meta['item']['start_url'] == self.write_for_us_url:
                if "start=50" not in next_page[0]: # you can change start param here for the write for us URL
                    yield r
            elif "start=50" not in next_page[0]: # This is for the rest of the urls
                yield r







































        # for r in results:
        #     ext = tldextract.extract(r)
        #     print("---------------------------extract tld",ext)
           
        #     if not (ext.domain in ['wordpress', 'pinterest'] or ext.suffix == 'it' or ext.domain in self.domains_scraped):
        #         self.domains_scraped.append(ext.domain)
        #         yield {
        #             "website_url": r,
        #             "base_url": response.meta['item']['start_url'],
        #             "category": response.meta['item'].get('category') or 'None',
        #             'report_title': self.report_title
        #         }


      




        # if next_page != []:
        #     absolute_nextpageurl = "https://www.google.com" + next_page[0]
        #     print("ABSOULT next page----------------------------------->>>>>>>>", absolute_nextpageurl)

        #     r = Request(absolute_nextpageurl, dont_filter=True)
        #     item = {
        #         'start_url': response.meta['item']['start_url'],
        #         'category': response.meta['item'].get('category') or 'None',
        #         'report_title': self.report_title
        #     }
        #     print("-----------------------------------ITEM   222222 ", item)
        #     r.meta['item'] = item
        #     if response.meta['item']['start_url'] == self.write_for_us_url:
        #         if "start=100" not in next_page[0]: # you can change start param here for the write for us URL
        #             yield r
        #     elif "start=50" not in next_page[0]: # This is for the rest of the urls
        #         yield r
















