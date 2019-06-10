# -*- coding: utf-8 -*-
import scrapy
import re
from collections import OrderedDict
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCpin14, CCrecord, CCrecordLine


class ScrapSpider(CSVFeedSpider):
    """1 level crawling.
    Reads the pin feed csv file and parses the CC recorder
    for these pins.
    The pins can be 10 or 14 digit long
    """
    name = '2_pins_docs'                     # 1 means 1-level.
    allowed_domains = ['ccrecorder.org']
    start_urls = ['https://alxfed.github.io/docs/pin_feed3.csv']        # the list of PINs to be verified.
    headers = ['pin']
    DOCS_LIST_URL ='https://ccrecorder.org/parcels/show/parcel/'        # docs list request for record_number

    def parse_row(self, response, row):
        """
        Reads a row in csv and makes a request to the pin page
        :param response: the downloaded pin page
        :param row: a single PIN read from the pin feed file
        :return: yields a scrapy.Request to pin page
        """
        PIN_REQUEST_URL             = 'https://www.ccrecorder.org/parcels/search/parcel/result/?line='
        pin = row['pin']                                                # the name of the column defined in 'headers'
        yield scrapy.Request(url=PIN_REQUEST_URL + pin,
                             callback=self.parse_pin_page,
                             meta={'pin':pin})

    def parse_pin_page(self, response):
        """
        Parses the pin page, detects if there is none, detects if
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

        pin14 = CCrecord()           # the item

        # FUCK YOU, IDIOT DON GUERNSEY ! (https://www.linkedin.com/in/don-guernsey-8412663/)
        response = response.replace(body=re.sub('>\s*<', '><',
                                                response.body.replace('\n', ''),
                                                0, re.M))
        # The stupid fuck dumped this shit on the page to make in 'unscrapable'. :) Imbecile peasant from Indiana woods.

        NOT_FOUND = response.xpath(NO_PINS_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No PINs'):                         # No PINs?
                pin = response.meta['pin']
                if len(pin) < 14:
                    pin = pin + '0000'
                pin14['pin'] = pin
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
                record_number  = line.xpath(RECORD_NUMBER_XPATH).re('[.0-9]+')[0]
                pin14['record_number'] = record_number
                pin14['pin_status']     = 'valid'
                yield scrapy.Request(url=self.DOCS_LIST_URL+record_number+'/',
                                     callback=self.parse_docs_page,
                                     meta={'pin14': pin14})

    def parse_docs_page(self, response):
        """
        Parses the page with the history of transactions
        and finds identifiers of docs and owners/entities.
        :param response:
        :return:
        """
        DOCS_LIST_LINE_XPATH = '//table[@id="docs_table"]/*[@id="docs_body"]//tr'

        record = CCrecord()                     # instantiate a new record
        record['pin'] = response.meta['pin14']['pin']
        record['pin_status'] = 'valid'
        record['street_address'] = response.meta['pin14']['street_address']
        record['record_number'] = response.meta['pin14']['record_number']
        record['city'] = response.meta['pin14']['city']

        pin_docs_list = OrderedDict()

        lines_list = response.xpath(DOCS_LIST_LINE_XPATH)
        # a frame for the complete list of search results should be here. It and then the iteration.
        for index, line in enumerate(lines_list):  # every doc_list_line one by one
            doc_list_line = CCrecordLine()
            doc_list_line['date'] = line.xpath('td[1]/text()').get()
            doc_list_line['doc_type'] = line.xpath('td[2]/text()').get()
            doc_list_line['doc_num'] = line.xpath('td[3]/text()').get()
            doc_list_line['doc_url_num'] = line.xpath('td[3]/a/@href').re('[-.0-9]+')[0]
            doc_list_line['consideration'] = line.xpath('td[4]/text()').get()
            # cycle inside the docs1_table
            # cycle inside the docs2_table
            # cycle inside the docs3_table
            # buttons are useless, they have the same doc_url_num in them.
            pin_docs_list.update({str(index + 1): doc_list_line})
            print('ok')
        else:  # finished reading the list of search results time to return it
            record['docs'] = pin_docs_list
            yield record




# finished on June 7-th, 2019.