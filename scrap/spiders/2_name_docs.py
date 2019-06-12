# -*- coding: utf-8 -*-
import scrapy
import re
from collections import OrderedDict
from scrapy.spiders import CSVFeedSpider
from scrap.items import CCnameSearchResultS, CCnameSearchResult, CCnameDoc


def pre_processed_name(self, name):
    """Take all extra elements from the string
    and make it allcaps
    """
    name = name.replace(".',", '')
    name = name.replace(' ', '+')
    return name.upper()


class NamesSearchSpider(CSVFeedSpider):
    """
    Reads the name feed csv file and parses the CC recorder
    for these names.
    The names can be 10 or 14 digit long
    """
    name = '2_name_docs'
    allowed_domains = ['ccrecorder.org']
    start_urls = ['https://alxfed.github.io/docs/names_feed.csv']
    headers = ['name']
    # where are we sending these parameters
    NAME_REQUEST_URL = 'https://www.ccrecorder.org/recordings/search/name/result/?ln='
    NAME_DOCS_PAGE_URL = 'https://www.ccrecorder.org/recordings/show/idx_name/'

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

        name_search_result = CCnameSearchResult()
        name_search_result['requested_name'] = response.meta['name']

        NOT_FOUND = response.xpath(NO_NAMES_FOUND_RESPONSE_XPATH).get()  # what is there
        if NOT_FOUND:                                                   # ?  (can't do without this, because of None)
            if NOT_FOUND.startswith('No Docs'):                         # No names?
                name_search_result['name_status'] = 'not'
                yield name_search_result                                             # and get out of here.

            else:
                self.log('something is in the place of No Docs but it is not it')
                yield None

        else:                                                           # there is a name like that
            lines_list = response.xpath(NAMES_LIST_LINE_XPATH)
            # a frame for the complete list of search results should be here. It and then the iteration.
            for index, line in enumerate(lines_list):             # every name_search_result one by one
                name_search_result = CCnameSearchResult()
                name_search_result['requested_name'] = response.meta['name']
                name_search_result['requested_name_status'] = 'valid'
                name_search_result['name'] = line.xpath('td[1]/text()').get()
                name_search_result['trust_number'] = line.xpath('td[2]/text()').get()
                name_search_result['last_update'] = line.xpath('td[3]/text()').get()
                idx_name = line.xpath('td[4]/a/@href').re('[-.0-9]+')[0]  # Fuck you, Don Guernsey!
                name_search_result['idx_name'] = idx_name
                # go to the page of docs associated with the name and read it, then come back
                yield scrapy.Request(url=self.NAME_DOCS_PAGE_URL+idx_name+'/',
                                     callback=self.parse_name_docs_page(),
                                     meta={'name_search_result': name_search_result})


    def parse_name_docs_page(self, response):
        """
        Assembles the result from the line of the initial name search result
        and the items from the page it is pointing to.
        :param response:
        :return:
        """
        DOCS_NAME_LIST_XPATH = '//table[@id="docs_table"]/tbody[@id="doc_names_body"]/tr'

        name_search_result = CCnameSearchResult()
        name_search_result = response.meta['name_search_result']
        docs = OrderedDict()

        docs_list = response.xpath(DOCS_NAME_LIST_XPATH)
        for indu, doc in enumerate(docs_list):
            name_doc = CCnameDoc()
            name_doc['gte'] = doc.xpath('td[1]/text()').get()
            name_doc['gtr'] = doc.xpath('td[2]/text()').get()
            name_doc['doc_type'] = doc.xpath('td[3]/text()').get()
            name_doc['doc_num'] = doc.xpath('td[4]/text()').get()
            name_doc['date'] = doc.xpath('td[5]/text()').get()
            name_doc['trust_number'] = doc.xpath('td[6]/text()').get()
            name_doc['pin14'] = doc.xpath('td[7]/text()').get()
            name_doc['show_url'] = doc.xpath('td[8]/a/@href').re('[-.0-9]+')[0]
            docs.update({str(indu+1): name_doc})
        else:
            name_search_result['docs'] = docs
            yield name_search_result
