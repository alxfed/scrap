# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class CcrecorderPipeline(object):
    """
    Azure?
    """
    def process_item(self, item, spider):
        #print('I have been in the pipeline too. Do not worry')
        return item

