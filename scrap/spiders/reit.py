# -*- coding: utf-8 -*-
import scrapy


class ReitSpider(scrapy.Spider):
    name = 'reit'
    allowed_domains = ['sec.gov']
    start_urls = ['https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC=6798&owner=include&match=&start=1200&count=30']
    base_url = ['https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC=6798&owner=include&match=&start=']
    page_num = 1

    def parse(self, response):
        """Multipage parse with 100 items on page and incrementable URL
        """
        EMPTY_PAGE_XPATH = '//div[@class="noCompanyMatch"]/text()'
        CIK_XPATH = '//*[@id="seriesDiv"]/*[@summary="Results"]/tbody//tr'

        NO_COMPANY_MATCH = response.xpath(EMPTY_PAGE_XPATH).get()
        if NO_COMPANY_MATCH:
                if NO_COMPANY_MATCH.startswith('No matching companies'):
                    yield None
                else:
                    self.log('There is something in place of No matching companies but it is not it')
        else:
            company_list = response.xpath(CIK_XPATH)
            for company in company_list:


            next_page_url = self.base_url + r'{}&count=100'.format(str(100*page_num))
            yield scrapy.Request(url=next_page_url, callback=parse)
