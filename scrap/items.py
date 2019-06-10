# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SECcompany(scrapy.Item):
    cik = scrapy.Field()
    company = scrapy.Field()
    state = scrapy.Field()

class CCnameSearchResultS(scrapy.Item):
    requested_name = scrapy.Field()
    name_status = scrapy.Field()
    results = scrapy.Field()

class CCnameSearchResult(scrapy.Item):
    """A list of found results for a
    given name
    """
    name = scrapy.Field()
    trust_number = scrapy.Field()
    last_update = scrapy.Field()
    idx_name = scrapy.Field()

class CCname(scrapy.Item):
    """Names in the CC recorder database
    """
    name = scrapy.Field()
    idx_name = scrapy.Field()


class CCpin14(scrapy.Item):
    """pin14 item for pins spider
    """
    pin = scrapy.Field()
    pin_status = scrapy.Field()
    record_number = scrapy.Field()
    street_address = scrapy.Field()
    city = scrapy.Field()


class CCrecordLineName(scrapy.Item):
    """doc1_table item
    """
    name = scrapy.Field()
    type = scrapy.Field()


class CCrecordLineParcel(scrapy.Item):
    """doc2_table item
    """
    pin = scrapy.Field()
    address = scrapy.Field()


class CCrecordLineRelatedDoc(scrapy.Item):
    """doc3_table item
    """
    doc_number = scrapy.Field()
    url = scrapy.Field()


class CCrecordLine(scrapy.Item):
    """
    A single line in a list of documents of a record
    """
    date = scrapy.Field()
    doc_type = scrapy.Field()
    doc_num = scrapy.Field()
    doc_url_num = scrapy.Field
    consideration = scrapy.Field()
    names = scrapy.Field()
    parcels = scrapy.Field()
    related_docs = scrapy.Field()
    show_doc = scrapy.Field()


class CCrecord(scrapy.Item):
    """
    The complete record/list of events associated with a PIN
    """
    pin = scrapy.Field()
    pin_status = scrapy.Field()
    street_address = scrapy.Field()
    city = scrapy.Field()
    record_number = scrapy.Field()
    docs = scrapy.Field()

