# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity


class CcrecorderPipeline(object):
    """
    Azure?
    """
    row = 1
    def process_item(self, item, spider):
        #print('I have been in the pipeline too. Do not worry')

        return item


table_service = TableService(account_name='recorder',
                             account_key='76hLvt3Ij8A0zwEEguzCXxGG1BQcpYgqkQ+e8f21Nmg47ldLUCWRoBnuJgPlELE8GIcpjxRq1oR2wBKCOePwiQ==')

table_service.create_table('ccrecorder')

task = Entity()
task.PartitionKey = 'tasksSeattle'
task.RowKey = '002'
task.description = 'Wash the car'
task.priority = 100
table_service.insert_entity('ccrecorder', task)