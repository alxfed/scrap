# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCname


class RecordsSpider(CSVFeedSpider):
    """
    Reads the name feed csv file and parses the CC recorder
    for these names.
    The names can be 10 or 14 digit long
    """
    name = 'names'
    allowed_domains = ['ccrecorder.org']
    start_urls = ['https://alxfed.github.io/docs/names_feed.csv']
    headers = ['name']

    def pre_processing(self, name):
        """Take all extra elements from the string
        and make it allcaps
        """
        name = name.replace("',.", '')
        name = name.upper()
        name_string = name
        return name_string

    def parse_row(self, response, row):
        """
        Reads a row in csv and makes a request to the name page
        :param response: the downloaded name page
        :param row: a single name read from the name feed file
        :return: yields a scrapy.Request to name page
        """
        name_REQUEST_URL = 'https://www.ccrecorder.org/recordings/search/name/result/?ln='
        name = row['name']                                                # the name of the column defined in 'headers'
        yield scrapy.Request(url=name_REQUEST_URL + name, callback=self.parse_name_page, meta={'name':name})

    def parse_name_page(self, response):
        """
        Parses the name page, detects if there is none, detects if
        there are multiple names and their corresponding links on a page,
        jumps to those pages and scrapes their contence into a
        scrapy.item CCrecord
        :param response:
        :return: yields a record or a bunch of records
        """
        name_LIST_LINE_XPATH = '//*[@id="names_table"]/*[@id="objs_body"]/tr'  #//*[@id="objs_table"]
        name14_XPATH = '/td[1]/text()'
        STREET_ADDRESS_XPATH = '/td[2]/text()'
        CITY_XPATH = '/td[3]/text()'
        RECORD_NUMBER_XPATH = '/td[4]/a/@href'
        NO_nameS_FOUND_RESPONSE_XPATH = '//html/body/div[4]/div/div/div[2]/div/div/p[2]/text()' # where it can be

        # And now...
        name14 = CCname14()

        NOT_FOUND = response.xpath(NO_nameS_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No names'):                         # No names?
                name = response.meta['name']
                if len(name) < 14:
                    name = name + '0000'
                name14['name'] = name
                name14['name_status'] = 'not'
                #self.log('Not found name '+response.url)                 # Debug notification
                yield name14                                             # and get out of here.

            else:
                self.log('something is in the place of No names but it is not it')
                yield None

        else:                                                           # there is a name like that
            # Tried to iterate over selectors but it didn's work, this is a less elegant way
            lines_list = response.xpath(name_LIST_LINE_XPATH).getall()
            # extract the number(s) for the record(s), jump to the docs page
            # (as many times as necessary, come back every time when done
            for index, line in enumerate(lines_list):  # not to forget that 14 digit name gives 2 tables of results.
                linear = str(index+1)
                #self.log(line)
                line_xpath = '{}[{}]'.format(name_LIST_LINE_XPATH, linear)
                name14['name'] = response.xpath(line_xpath + name14_XPATH).get()
                name14['street_address'] = response.xpath(line_xpath + STREET_ADDRESS_XPATH).get()
                name14['city'] = response.xpath(line_xpath + CITY_XPATH).get().strip()             # strip removes trailing spaces
                name14['record_number'] = response.xpath(line_xpath + RECORD_NUMBER_XPATH).re('[.0-9]+')[0]
                name14['name_status'] = 'valid'
                #self.log(response.meta['name'])
                yield name14