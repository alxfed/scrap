# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.selector import Selector
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCname


def pre_processed_name(self, name):
    """Take all extra elements from the string
    and make it allcaps
    """
    name = name.replace("',.", '')
    name = name.replace(' ', '+')
    return name.upper()


class RecordsSpider(CSVFeedSpider):
    """
    Reads the name feed csv file and parses the CC recorder
    for these names.
    The names can be 10 or 14 digit long
    """
    name = 'company_names'
    allowed_domains = ['ccrecorder.org']
    start_urls = ['https://alxfed.github.io/docs/names_feed.csv']
    headers = ['co_name']

    def parse_row(self, response, row):
        """
        Reads a row in csv and makes a request to the name page
        :param response: the downloaded name page
        :param row: a single name read from the name feed file
        :return: yields a scrapy.Request to name page
        """
        name_REQUEST_URL = 'https://www.ccrecorder.org/recordings/search/name/result/?ln='
        name_var = row['co_name']                                                # the name of the column defined in 'headers'
        url_suffix = pre_processed_name(name_var)
        yield scrapy.Request(url=name_REQUEST_URL + url_suffix, callback=self.parse_name_page, meta={'name':name})

    def parse_name_page(self, response):
        """
        Parses the name page, detects if there is none, detects if
        there are multiple names and their corresponding links on a page,
        jumps to those pages and scrapes their contence into a
        scrapy.item CCrecord
        :param response:
        :return: yields a record or a bunch of records
        """
        NAMES_LIST_LINE_XPATH = '//table[@id="names_table"]/body[@id="objs_body"]//tr'  #//*[@id="objs_table"]
        name14_XPATH = '/td[1]/text()'
        STREET_ADDRESS_XPATH = '/td[2]/text()'
        CITY_XPATH = '/td[3]/text()'
        RECORD_NUMBER_XPATH = '/td[4]/a/@href'
        NO_NAMES_FOUND_RESPONSE_XPATH = '//html/body/div[4]/div/div/div[2]/div/div/p[2]/text()' # where it can be

        # And now...
        name = CCname()

        # FUCK YOU, IDIOT DON GUERNSEY ! (https://www.linkedin.com/in/don-guernsey-8412663/)
        response = response.replace(body=re.sub('>\s*<', '><',
                                                response.body.replace('\n', ''),
                                                0, re.M))
        # The stupid fuck dumped this shit on the page to make in 'unscrapable'. :) Imbecile peasant from Indiana woods.

        NOT_FOUND = response.xpath(NO_NAMES_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No names'):                         # No names?
                name = response.meta['name']
                if len(name) < 14:
                    name = name + '0000'
                name['name'] = name
                name['name_status'] = 'not'
                yield name                                             # and get out of here.

            else:
                self.log('something is in the place of No names but it is not it')
                yield None

        else:                                                           # there is a name like that
            lines_list = response.xpath(NAMES_LIST_LINE_XPATH)
            for line in lines_list:
                line_xpath = '{}[{}]'.format(name_LIST_LINE_XPATH, linear)
                name['name'] = response.xpath(line_xpath + name14_XPATH).get()
                name['street_address'] = response.xpath(line_xpath + STREET_ADDRESS_XPATH).get()
                name['city'] = response.xpath(line_xpath + CITY_XPATH).get().strip()             # strip removes trailing spaces
                name['record_number'] = response.xpath(line_xpath + RECORD_NUMBER_XPATH).re('[.0-9]+')[0]
                name['name_status'] = 'valid'
                #self.log(response.meta['name'])
                yield name