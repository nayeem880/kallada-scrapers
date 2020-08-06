from urllib.parse import quote

import scrapy
from scrapy.http import Request
import tldextract


class GuestpostscraperSpider(scrapy.Spider):
    name = 'guestpostscraper'
    allowed_domains = ['google.com']
    start_urls = []
    scraped_urls = []
    count = 0
    domains_scraped = []

    queries = []
    guestpost_keywords = ['intitle:"write for us"', 'intitle:"Become a contributor"',
                          'intitle:"Submission guidelines"', 'intitle:"Submit guest post"',
                          'intitle:"Guest post guidelines"', 'intitle:"Guest bloggers wanted"',
                          'intitle:"Submission guidelines"']

    write_for_us_url = ''

    def start_requests(self):
        for seed_keyword in self.seed_keywords.split(','):
            self.write_for_us_url = 'https://www.google.com/search?q=' + quote(seed_keyword + ' intitle:"write for us"')

            for i in self.guestpost_keywords:
                tmp = seed_keyword + " " + i
                self.queries.append(tmp)

            # unicode_query = generate_unicode_queries(queries)
            for i in self.queries:
                i = quote(i)
                i = 'https://www.google.com/search?q=' + i
                self.start_urls.append(i)

            for url in self.start_urls:
                item = {'start_url': url}
                request = Request(url, dont_filter=True)
                # set the meta['item'] to use the item in the next call back
                request.meta['item'] = item
                yield request

    def parse(self, response):
        results = response.xpath('//*[@id="rso"]/div[*]/div/div[1]/a/@href').extract()
        next_page = response.xpath('//*[@id="pnnext"]/@href').extract()
        absolute_nextpageurl = ""

        self.scraped_urls = self.scraped_urls + results

        for r in results:
            ext = tldextract.extract(r)
            if not (ext.domain in ['wordpress', 'pinterest'] or ext.suffix == 'it' or ext.domain in self.domains_scraped):
                self.domains_scraped.append(ext.domain)
                yield {
                    "website_url": r,
                    "base_url": response.meta['item']['start_url']
                }

        if next_page != []:
            absolute_nextpageurl = "https://www.google.com" + next_page[0]
            r = Request(absolute_nextpageurl)
            item = {'start_url': response.meta['item']['start_url']}
            r.meta['item'] = item
            if response.meta['item']['start_url'] == self.write_for_us_url:
                if "start=100" not in next_page[0]: # you can change start param here for the write for us URL
                    yield r
            elif "start=50" not in next_page[0]: # This is for the rest of the urls
                yield r



















