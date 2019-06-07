# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.selector import Selector
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCnameSearchResult


def pre_processed_name(self, name):
    """Take all extra elements from the string
    and make it allcaps
    """
    name = name.replace("',.", '')
    name = name.replace(' ', '+')
    return name.upper()


class NamesSearchSpider(CSVFeedSpider):
    """
    Reads the name feed csv file and parses the CC recorder
    for these names.
    The names can be 10 or 14 digit long
    """
    name = '1_names_search'
    allowed_domains = ['ccrecorder.org']
    start_urls = ['https://alxfed.github.io/docs/names_feed4.csv']
    headers = ['name']
    # where are we sending these parameters
    NAME_REQUEST_URL = 'https://www.ccrecorder.org/recordings/search/name/result/?ln='

    def parse_row(self, response, row):
        """
        Reads a row in csv and makes a request to the name page
        :param response: the downloaded name page
        :param row: a single name read from the name feed file
        :return: yields a scrapy.Request to name page
        """
        # the name of the column defined in 'headers'
        name = row['name']

        # transform it for a URL
        name_var = pre_processed_name(self, name)

        # make a request with a transformed name, but pass the original name in meta
        yield scrapy.Request(url=self.NAME_REQUEST_URL + name_var,
                             callback=self.parse_name_page,
                             meta={'name':name})

    def parse_name_page(self, response):
        """
        Parses the name search result page, detects if there are none, detects if
        there are multiple names and their corresponding links on a page.
        :param response:
        :return: yields a record or a bunch of records
        """
        NAMES_LIST_LINE_XPATH = '//table[@id="objs_table"]/tbody[@id="objs_body"]//tr'  #//*[@id="objs_table"]
        name14_XPATH = '/td[1]/text()'
        STREET_ADDRESS_XPATH = '/td[2]/text()'
        CITY_XPATH = '/td[3]/text()'
        RECORD_NUMBER_XPATH = '/td[4]/a/@href'
        NO_NAMES_FOUND_RESPONSE_XPATH = '//div[@class="card-body"]/p/text()' # where it can be

        # And now...
        name_search_result = CCnameSearchResult()

        # FUCK YOU, IDIOT DON GUERNSEY ! (https://www.linkedin.com/in/don-guernsey-8412663/)
        response = response.replace(body=re.sub('>\s*<', '><',
                                                response.body.replace('\n', ''),
                                                0, re.M))
        # The stupid fuck dumped this shit on the page to make in 'unscrapable'. :) Imbecile peasant from Indiana woods.

        NOT_FOUND = response.xpath(NO_NAMES_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No Docs'):                         # No names?
                name_search_result['name'] = response.meta['name']
                name_search_result['name_status'] = 'not'
                yield name_search_result                                             # and get out of here.

            else:
                self.log('something is in the place of No Docs but it is not it')
                yield None

        else:                                                           # there is a name like that
            lines_list = response.xpath(NAMES_LIST_LINE_XPATH)
            # a frame for the complete list of search results should be here.
            for line in lines_list:             # every name_search_result one by one
                line_xpath = '{}[{}]'.format(NAMES_LIST_LINE_XPATH, linear)
                name_search_result['name'] = response.xpath(line_xpath + name14_XPATH).get()
                name_search_result['street_address'] = response.xpath(line_xpath + STREET_ADDRESS_XPATH).get()
                name_search_result['city'] = response.xpath(line_xpath + CITY_XPATH).get().strip()             # strip removes trailing spaces
                name_search_result['record_number'] = response.xpath(line_xpath + RECORD_NUMBER_XPATH).re('[.0-9]+')[0]
                name_search_result['name_status'] = 'valid'
                #self.log(response.meta['name'])
                yield name_search_result