# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.loader import ItemLoader
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCnameSearchResultS, CCnameSearchResult


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
        NO_NAMES_FOUND_RESPONSE_XPATH = '//div[@class="card-body"]/p/text()' # where it can be

        # FUCK YOU, IDIOT DON GUERNSEY ! (https://www.linkedin.com/in/don-guernsey-8412663/)
        response = response.replace(body=re.sub('>\s*<', '><',
                                                response.body.replace('\n', ''),
                                                0, re.M))
        # The stupid fuck dumped this shit on the page to make in 'unscrapable'. :) Imbecile peasant from Indiana woods.

        search_results = CCnameSearchResultS()
        search_results['requested_name'] = response.meta['name']

        NOT_FOUND = response.xpath(NO_NAMES_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No Docs'):                         # No names?
                search_results['name_status'] = 'not'
                yield search_results                                             # and get out of here.

            else:
                self.log('something is in the place of No Docs but it is not it')
                yield None

        else:                                                           # there is a name like that
            search_results['name_status'] = 'valid'
            lines_list = response.xpath(NAMES_LIST_LINE_XPATH)
            # a frame for the complete list of search results should be here. It and then the iteration.
            for index, line in enumerate(lines_list):             # every name_search_result one by one
                name_search_result = ItemLoader(CCnameSearchResult(), line)
                name_search_result.add_xpath('name', '/td[1]/text()')
                name_search_result.add_xpath('trust_number', '/td[2]/text()')
                name_search_result.add_xpath('last_update', '/td[3]/text()')
                name_search_result.add_xpath('idx_name', '/td[3]/a/@href', re='[.0-9]+')
                search_results['results_list'].update({str(index+1): name_search_result.load_item()})
            else:                   # finished reading the list of search results time to return it
                yield search_results