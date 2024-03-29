'''
Alex Haas
functions that make the calls and then separate functions that prepare data for use by FE
'''
from werkzeug.security import check_password_hash
from pymongo import MongoClient, DESCENDING, ReturnDocument
from datetime import datetime
from bson.objectid import ObjectId


dbContracts = 'ab_dbcontracts'
dbGames = 'ab_dbgames'
dbLogs = 'ab_dblogs'
dbSiteGen = 'ab_dbsitegen'
dbTokens = 'ab_db_e_r_t'
dbUploads = 'ab_dbuploads'
dbUsers = 'ab_dbusers'
db_mc = MongoClient()
active_tokens = 'activetokens'
expired_tokens = 'expiredtokens'
strange_tokens = 'strangetokens'
used_tokens = 'usedtokens'
ccontracts = 'ccontracts'
cusers = 'cusers'
login_log = 'loginlog'
logout_log = 'logoutlog'
samples = 'samples'


dict_template = {
                'active': True,
                'email': 'aaSDaa@aaaSDa.com',
                'pass': 'aaaassssddddffff',
                'uName': 'somename',
                'joinDate': 'some date for sure 2',
                'orders': []
            }


def c_accept_offer(contractid_obj, bhunterid_obj, bhunter_uname, bhunter_offer, clog_obj, now_time):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    result = dbc.update_one({'_id': contractid_obj},
                            {'$set': {'bhunter': bhunterid_obj,
                                      'phase': 'inprogress',
                                      'bounty': bhunter_offer,
                                      'bhunter_uname': bhunter_uname,
                                      'timeline.1.time': now_time},
                             '$push': {'clog': clog_obj}})
    return result


def c_create_ip(contract_id, ip_object):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$push': {'iparties': ip_object}})


def c_send_chat(contract_id_obj, chatnewmsguser, chat_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    print(chatnewmsguser)
    return dbc.update_one({'_id': contract_id_obj}, {'$push': {'chat': chat_obj},
                                                     '$set': {chatnewmsguser: True}})


def cancel_contract(contract_id):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.delete_one({'_id': ObjectId(contract_id)})


def create_contract(user_obj):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    # check if user exists
    if dbc.find_one(user_obj['owner']):
        db = db_mc[dbContracts]
        dbc = db[ccontracts]
        result = dbc.insert_one(user_obj)
        return result
    return None

# returns pymongo InsertOneResult(inserted_id: Any, acknowledged: bool)
def create_user(user_template):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    email_result = dbc.find_one({'email': user_template['email']})
    username_result = dbc.find_one({'uName': user_template['uName']})
    if email_result or username_result:
        class Temp_obj:
            def __init__(self):
                self.inserted_id = None
                self.acknowledged = False
        return Temp_obj()
    else:
        return dbc.insert_one(user_template)


def delete_active_token(email_token):
    db = db_mc[dbTokens]
    dbc = db[active_tokens]
    return dbc.find_one_and_delete({'token': email_token})


def get_active_token(email_token):
    db = db_mc[dbTokens]
    dbc = db[active_tokens]
    return dbc.find_one({'token': email_token})


def get_all_open():
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    contract_cursor = dbc.find({'phase': 'open'})
    if contract_cursor:
        return list(contract_cursor)
    return None


'''
INCOMPLETE
returns object if True, None if False
'''


def get_auth_user(email, password, tz_offset):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    user_record = dbc.find_one({'email': email}, {
        # '_id': 1,
        'email': 1,
        # 'uName': 1,
        'pass': 1
    })
    if user_record and check_password_hash(user_record['pass'], password):
        user_record = dbc.find_one_and_update({'email': email}, {'$set': {'tz_offset': tz_offset}}, return_document=ReturnDocument.AFTER)
        if user_record:
            return [str(user_record['_id']), email, user_record['uName'], user_record['_id'], user_record['tz_offset']]
    else:
        return None


def get_auth_user_no_tz():
    pass


def get_expired_token(email_token):
    db = db_mc[dbTokens]
    dbc = db[expired_tokens]
    return dbc.find_one({'token': email_token})


# returns contract or None
def c_get_contract(contract_id):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.find_one({'_id': ObjectId(contract_id)})


# MAKE THIS USE ONE QUERY WITH AGGREGATION... MAYBE BATCHES?
def c_get_contract_account(contract_id, nowtime, user_id):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    # AGGREGATION ...
    # result =  dbc.find_one_and_update({'_id': contract_id},
    #                                [{'$bucket': {
    #                                    '$groupBy': 'owner',
    #                                }}])
    # print(result)
    # return result


def get_contracts_top_10():
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    contract_cursor = dbc.find({'phase': 'open'}).limit(10)
    if contract_cursor:
        return contract_cursor
    return None


def get_rating_obj(contract_id):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.find_one({'_id': contract_id}, {
        '_id': 1,
        'bhunter': 1,
        'owner': 1,
        'reviews': 1
    })


def get_sesh(userid):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    user_record = dbc.find_one({'_id': ObjectId(userid)}, {
        '_id': 1,
        'email': 1,
        'tz_offset': 1,
        'uName': 1
    })
    if user_record:
        temp_array = [userid, user_record['email'], user_record['uName'], user_record['_id'], user_record['tz_offset']]
        return temp_array
    else:
        return []


def get_strange_token(email_token):
    db = db_mc[dbTokens]
    dbc = db[strange_tokens]
    return dbc.find_one({'token': email_token})


def get_used_token(email_token):
    db = db_mc[dbTokens]
    dbc = db[used_tokens]
    return dbc.find_one({'token': email_token})


def get_user(user_id):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    user_record = dbc.find_one({'_id': ObjectId(user_id)}, {
        'pass': 0
    })# add filter?
    return user_record


def get_user_contracts(userid_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    user_orders = dbc.find({"$or": [{"owner": userid_obj}, {"bhunter": userid_obj},
                                    {'$and': [{'phase': 'open'}, {'iparties.bhunter': userid_obj}]}]})
    return user_orders


def get_username(userid_obj):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    user_name = dbc.find_one({'_id': ObjectId(userid_obj)}, {
        'uName': 1
    })
    return user_name


def c_set_disputed(contract_id, clog_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'disputed'}, '$push': {'clog': clog_obj}})


def c_set_sampleUp(contract_id, loc_string):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': ObjectId(contract_id)}, {'$set': {'sampleUp': loc_string}})


def c_submit_approval(contract_id, clog_obj, efbonusyon):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'approved', 'efbonusyon': efbonusyon}, '$push': {'clog': clog_obj}})


def c_submit_successful(contract_id, clog_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'successful'}, '$push': {'clog': clog_obj}})


def c_getset_lvbhunter(contract_id, time):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.find_one_and_update({'_id': contract_id}, {'$set': {'lvbhunter': time, 'chatnewmsgbhunter': False}})


def c_getset_lvowner(contract_id, time):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.find_one_and_update({'_id': contract_id}, {'$set': {'lvowner': time, 'chatnewmsgowner': False}})


def c_set_open(contract_id, clog_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'open'}, '$push': {'clog': clog_obj}})


def c_set_rating(contract_id, clog_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'rating'}, '$push': {'clog': clog_obj}})


def c_submit_gvalidation(contract_id, clog_obj, filename):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    result = dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'gradevalidation', 'gsubmission': filename}, '$push': {'clog': clog_obj}})
    return result


def c_submit_assignment(contract_id, clog_obj, filename):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$set': {'phase': 'validation', 'asubmission': filename}, '$push': {'clog': clog_obj}})


def c_submit_rating_c(contract_id, review_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$push': {'reviews': review_obj}})


def c_submit_rating_u(user_id, review_obj):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    return dbc.update_one({'_id': user_id}, {'$push': {'reviewHistory': review_obj}})


def c_update_clog(contract_id, clog_obj):
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    return dbc.update_one({'_id': contract_id}, {'$push': {'clog': clog_obj}})


def check_size():
    db = db_mc[dbContracts]
    dbc = db[ccontracts]
    print(dbc.stats())


def log_userlogin(user_id):
    db = db_mc[dbLogs]
    dbc = db[login_log]
    result = dbc.insert_one({
        'time': datetime.fromisoformat(datetime.utcnow().isoformat()),
        'userid': user_id
    })
    if result.acknowledged:
        print(str(user_id) + ' has logged in')
    else:
        print('failed to log user login for ' + str(user_id))


def log_userlogout(user_id):
    db = db_mc[dbLogs]
    dbc = db[logout_log]
    result = dbc.insert_one({
        'time': datetime.fromisoformat(datetime.now().isoformat()),
        'userid': user_id
    })
    if result.acknowledged:
        print(str(user_id) + ' has logged out')
    else:
        print('failed to log user logout for ' + str(user_id))


def upload_sample(sample_obj):
    db = db_mc[dbUploads]
    dbc = db[samples]
    return dbc.insert_one(sample_obj)


def set_activetoken(email_token_obj):
    db = db_mc[dbTokens]
    dbc = db[active_tokens]
    return dbc.insert_one(email_token_obj)


def set_emailconfirmed(email, message_obj, user_id):
    db = db_mc[dbUsers]
    dbc = db[cusers]
    return dbc.find_one_and_update({'_id': user_id, 'email': email},
                                   {'$set': {'emailconfirmed': True}, '$push': {'userlog': message_obj}},
                                   return_document=ReturnDocument.AFTER)


def set_strange_token(time, token):
    db = db_mc[dbTokens]
    dbc = db[strange_tokens]
    return dbc.insert_one({
        'time': time,
        'token': token
    })


def set_used_token(token_doc):
    db = db_mc[dbTokens]
    dbc = db[used_tokens]
    return dbc.insert_one(token_doc)
