# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.selector import Selector
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCpin14


class ScrapSpider(CSVFeedSpider):
    """1 level crawling.
    Reads the pin feed csv file and parses the CC recorder
    for these pins.
    The pins can be 10 or 14 digit long
    """
    name = '1_address_pins'                     # 1 means 1-level.
    allowed_domains = ['ccrecorder.org']
    start_urls = ['https://alxfed.github.io/docs/address_feed1.csv']        # the list of PINs to be verified.
    headers = ['address']

    def parse_row(self, response, row):
        """
        Reads a row in csv and makes a request to the pin page
        :param response: the downloaded pin page
        :param row: a single PIN read from the pin feed file
        :return: yields a scrapy.Request to pin page
        """
        ADDRESS_REQUEST_URL = 'https://www.ccrecorder.org/parcels/search/parcel/result/?line='
        address = row['address']                                           # the name of the column defined in 'headers'
        yield scrapy.Request(url=ADDRESS_REQUEST_URL + address,
                             callback=self.parse_address_page,
                             meta={'requested_address':address})

    def parse_address_page(self, response):
        """
        Parses the address page, detects if there is none, detects if
        there are multiple pins and their corresponding links on a page.
        :param response:
        :return: yields a record or a bunch of records
        """
        PIN_LIST_LINE_XPATH         = '//table[@id="pins_table"]/*[@id="objs_body"]//tr'  #//*[@id="objs_table"]
        PIN14_XPATH                 = 'td[1]/text()'
        STREET_ADDRESS_XPATH        = 'td[2]/text()'
        CITY_XPATH                  = 'td[3]/text()'
        RECORD_NUMBER_XPATH         = 'td[4]/a/@href'
        NO_PINS_FOUND_RESPONSE_XPATH = '//html/body/div[4]/div/div/div[2]/div/div/p[2]/text()' # where it can be

        pin14 = CCpin14()           # the item

        # FUCK YOU, IDIOT DON GUERNSEY ! (https://www.linkedin.com/in/don-guernsey-8412663/)
        response = response.replace(body=re.sub('>\s*<', '><',
                                                response.body.replace('\n', ''),
                                                0, re.M))
        # The stupid fuck dumped this shit on the page to make in 'unscrapable'. :) Imbecile peasant from Indiana woods.

        NOT_FOUND = response.xpath(NO_PINS_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No Addresses'):                         # No PINs?
                street_address = response.meta['requested_address']
                pin14['requested_address'] = street_address
                pin14['street_address'] = street_address
                pin14['pin_status'] = 'not'
                yield pin14                                             # and get out of here.

            else:
                self.log('something is in the place of No PINs but it is not it')
                yield None

        else:                                                           # there is a PIN like that
            # Tried to iterate over selectors but it didn's work, this is a less elegant way
            lines_list = response.xpath(PIN_LIST_LINE_XPATH)
            # extract the number(s) for the record(s), jump to the docs page
            # (as many times as necessary, come back every time when done
            for line in lines_list:
                pin14['pin']            = line.xpath(PIN14_XPATH).get()
                pin14['street_address'] = line.xpath(STREET_ADDRESS_XPATH).get()
                pin14['city']           = line.xpath(CITY_XPATH).get().strip()
                pin14['record_number']  = line.xpath(RECORD_NUMBER_XPATH).re('[.0-9]+')[0]
                pin14['pin_status']     = 'valid'
                yield pin14


# finished on June 7-th, 2019.