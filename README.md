First of all, navigate to the `spiders` folder using `cd extract_emails` and `cd spiders`. Then run "guestpostscraper" spider for getting the Opportunities for given keyword. Just type:

`scrapy crawl guestpostscraper -a seed_keywords=yoga,meditation` 

and press enter. Replace "yoga" and "meditation" by your own choosen keyword and keep all the keyword comma separated. For example: seed_keywords=yoga training,meditation course,meditation blog,meditation etc

Finally, run get_email spider to get the email from find opportunities web urls.
Type `scrapy crawl get_emails` for get the emails stored in get_emails.csv file in the "spiders" directory
