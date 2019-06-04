# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.loader import ItemLoader
from scrap.items import SECcompany


class ReitSpider(scrapy.Spider):
    name = '6552subdividers'
    allowed_domains = ['sec.gov']
    start_urls = ['https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC=6552&owner=include&match=&start=1&count=100']
    base_url = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC=6552&owner=include&match=&start='
    page_num = 1

    def parse(self, response):
        """Multipage parse with 100 items on page and incrementable URL
        """
        EMPTY_PAGE_XPATH = '//div[@class="noCompanyMatch"]/text()'
        COMPANY_LIST_XPATH = '//div[@id="seriesDiv"]/table[@summary="Results"]//tr'
        CIK_XPATH = 'td[@scope="row"][1]/a/text()'

        # minify html
        response = response.replace(body=re.sub('>\s*<', '><',
                                                response.body.replace('\n', ''),
                                                0, re.M))
        # minify html

        NO_COMPANY_MATCH = response.xpath(EMPTY_PAGE_XPATH).get()
        if NO_COMPANY_MATCH:
                if NO_COMPANY_MATCH.startswith('No matching companies'):
                    yield None
                else:
                    self.log('There is something in place of No matching companies but it is not it')
        else:
            company_list = response.xpath(COMPANY_LIST_XPATH)
            for company in company_list:
                not_header = company.xpath(CIK_XPATH).get()
                if not_header:
                    filing = ItemLoader(SECcompany(), company)
                    filing.add_xpath('cik',     CIK_XPATH)
                    filing.add_xpath('company', 'td[@scope="row"][2]/text()')
                    filing.add_xpath('state',   'td[@scope="row"][3]/a/text()')
                    yield filing.load_item()

            tail_url = r'{}&count=100'.format(str(100*self.page_num))
            self.page_num = self.page_num +1
            yield scrapy.Request(url=self.base_url + tail_url, callback=self.parse)
