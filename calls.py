'''
Alex Haas
functions that make the calls and then separate functions that prepare data for use by FE
'''
from pymongo import MongoClient, DESCENDING
import datetime


dbOrders = 'ab-dborders'
dbUsers = 'ab-dbusers'
dbSiteGen = 'ab-dbsitegen'
dbGames = 'ab-dbgames'
db_mc = MongoClient()


'''
Which ones will be chosen?
'''
def get_orders_top():
    db = db_mc[dbOrders]
    dbc = db["corders"]
    temp_array = list(dbc.find({}, {
        "_id": 0,
        "orderID": 1,
        "dateOpen": 1,
        "level": 1,
        "subject": 1,
        "status": 1,
        "contract.commitment": 1,
        "contract.finalPrice": 1
    }).limit(5))
    return temp_array