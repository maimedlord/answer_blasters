import calls
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import pytz
from werkzeug.utils import secure_filename
from user import User
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from flask import url_for


urlsafetimedserializer = 'thisisaterriblesecret'
urlsafetimedserializersalt = 'somesaltthisis'


def get_contracts_top():
    contracts_data = calls.get_contracts_top_10()
    if contracts_data:
        contracts_data = list(contracts_data)
    return contracts_data


def get_user_record(user_id):
    user_record = calls.get_user(ObjectId(user_id))
    if user_record == {"error": "no record found"}:
        return {}
    else:
        return user_record


def get_user_record_l(email, password):
    user_record = calls.get_user_record(email, password)
    if user_record == {"error": "no record found"}:
        return {}
    else:
        return user_record


def prc_accept_offer(bhunter_id, bhunter_uname, contract_id, bhunter_offer):
    clog_obj = {
        'event': 'bounty hunter offer accepted and phase set to inprogress',
        'time': datetime.utcnow()
    }
    result = calls.c_accept_offer(ObjectId(contract_id), ObjectId(bhunter_id), bhunter_uname, float(bhunter_offer), clog_obj, datetime.utcnow())
    if result.acknowledged:
        return True
    return None

def prc_get_contract_account(contract_id, user_id):
    result = calls.c_get_contract(ObjectId(contract_id))
    # also updates chat:
    if result:
        if result['bhunter'] == ObjectId(user_id):
            return calls.c_getset_lvbhunter(ObjectId(contract_id), datetime.utcnow())
        if result['owner'] == ObjectId(user_id):
            return calls.c_getset_lvowner(ObjectId(contract_id), datetime.utcnow())
    return result



def prc_create_ip(contract_id, bhunter_user_id, bhunter_uname, offer):
    ip_object = {
        'bhunter': bhunter_user_id,
        'bhunter_uname': bhunter_uname,
        'offer': offer,
        'time': datetime.utcnow()
    }
    return calls.c_create_ip(contract_id, ip_object)


# need mechanism to alert other use of chat...
def prc_send_chat(contract_id, userid, username, chatnewmsguser, message, mood):
    nowtime = datetime.utcnow()
    result = calls.c_send_chat(ObjectId(contract_id), chatnewmsguser, {'message': message,
                                                                       'mood': mood,
                                                                       'time': nowtime,
                                                                       'user': ObjectId(userid),
                                                                       'username': username})
    if result:
        if result.acknowledged:
            return True
    return None


def prc_set_disputed(contract_id, reason):
    # need to also update changelog and message to both users...
    # what phase is contract in when set to dispute?
    # alert admin to look at contract and make a finding/judgement.
    # return calls.c_set_disputed(ObjectId(contract_id))
    result = calls.c_set_disputed(ObjectId(contract_id), {
        'event': reason,
        'time': datetime.utcnow()
    })
    if result.acknowledged:
        #  stuff to do...???
        pass
    return result


def prc_set_rating(contract_id):
    result = calls.c_set_rating(ObjectId(contract_id), {
        'event': 'rating: bhunter approved grade proof',
        'time': datetime.utcnow()
    })
    if result.acknowledged:
        return True
    return False


def prc_set_successful(contract_id):
    result = calls.c_submit_successful(ObjectId(contract_id), {
        'event': 'successful: both users have submitted their ratings',
        'time': datetime.utcnow()
    })
    if result.acknowledged:
        #  stuff to do...???
        return True
    return None


def prc_set_open(contract_id):
    result = calls.c_set_open(ObjectId(contract_id), {
        'event': 'contract set to \'open\'',
        'time': datetime.utcnow()
    })
    if result.acknowledged:
        #  stuff to do...???
        return True
    return None


# needs to have option for bhunter to resubmit if owner finds work not to par
# still needs checkboxes...
def prc_yon_asubmission(form_dict, contract_id):
    # was efbonus deadline satsified/

    # bhunter gets paid
    # once paid, update database:
    if len(form_dict) > 0:
        yon = form_dict['s_d_yon']
        if yon =='false':
            # accept checkboxes that map to reasons why user feels bhunter's submission was deficient...
            result = prc_set_disputed(ObjectId(contract_id),
                                      'disputed: adjust function to input reasons why bhunters submission was '
                                      'deficient to owner')
            if result.acknowledged:
                # stuff to do...
                return True
        if yon == 'true':
            nowtime = datetime.utcnow()
            # check if submitted before efbonus:
            contract_obj = calls.c_get_contract(ObjectId(contract_id))
            # submit approval after checking if efbonus deadline satisfied:
            if contract_obj['efbonusyon'] and nowtime <= contract_obj['timeline'][5]['time']:
                result = calls.c_submit_approval(ObjectId(contract_id), {
                    'event': 'assignment approved and efbonus deadline satisfied',
                    'time': nowtime
                }, True)
            else:
                result = calls.c_submit_approval(ObjectId(contract_id), {
                    'event': 'assignment approved and efbonus NOT satisfied',
                    'time': nowtime
                }, False)
            if result.acknowledged:
                #  stuff to do...
                return True
    return None


def prc_submit_gvalidation(contract_id, filename):
    if filename is not None:
        result = calls.c_submit_gvalidation(ObjectId(contract_id), {
            'event': 'owner has submitted grade proof',
            'time': datetime.utcnow()
        }, filename)
        # other stuff like alerts, etc. ...
        if result.acknowledged:
            return True
        return None
    result = calls.c_set_rating(ObjectId(contract_id), {
        'event': 'gvalidation-skipto-rating: owner has claimed the grade was sufficient!',
        'time': datetime.utcnow()
    })
    # other stuff here like releasing egbonus...
    if result.acknowledged:
        return True
    return None


def prc_submit_assignment(contract_id, filename):
    result = calls.c_submit_assignment(ObjectId(contract_id), {
        'event': 'assignment submitted and waiting validation',
        'time': datetime.utcnow()
    }, filename)
    if result.acknowledged:
        return True
    return None


def prc_submit_rating_c(comment, contract_id, rating, user_id):
    now_time = datetime.utcnow()
    review_obj = {
        'comment': comment,
        'rating': float(rating),
        'time': now_time,
        'user': ObjectId(user_id)
    }
    rating_obj = calls.get_rating_obj(ObjectId(contract_id))
    if len(rating_obj['reviews']) == 0:
        result = calls.c_submit_rating_c(ObjectId(contract_id), review_obj)
        if result.matched_count > 0 and result.matched_count == result.modified_count:
            return True
    if len(rating_obj['reviews']) == 1:
        if rating_obj['reviews'][0]['user'] != ObjectId(user_id):
            # update contract reviews
            # rating submitted to contract
            result = calls.c_submit_rating_c(ObjectId(contract_id), review_obj)
            if result.matched_count > 0 and result.matched_count == result.modified_count:
                # user1 from passed in values
                user_review_obj1 = {
                    'comment': comment,
                    'contract': ObjectId(contract_id),
                    'rating': float(rating),
                    'reviewer': ObjectId(user_id),
                    'time': now_time
                }
                # user2 from rating_obj
                user_review_obj2 = {
                    'comment': rating_obj['reviews'][0]['comment'],
                    'contract': rating_obj['_id'],
                    'rating': float(rating_obj['reviews'][0]['rating']),
                    'reviewer': rating_obj['reviews'][0]['user'],
                    'time': now_time
                }
                other_user = rating_obj['bhunter']
                if other_user == ObjectId(user_id):
                    other_user = rating_obj['owner']
                result1a = calls.c_submit_rating_u(ObjectId(user_id), user_review_obj1)
                result1b = calls.c_submit_rating_u(ObjectId(user_id), user_review_obj2)
                result2a = calls.c_submit_rating_u(other_user, user_review_obj1)
                result2b = calls.c_submit_rating_u(other_user, user_review_obj2)
                result3 = calls.c_submit_successful(rating_obj['_id'], {
                    'event': 'successful: ratings submitted by both users',
                    'time': now_time
                })
                if result1a.acknowledged and result1b.acknowledged and result2a.acknowledged and result2b.acknowledged and result3.acknowledged:
                    return True
                return None
            # update individual user reviewHistory for BOTH reviews
            # update phase of contract
    return None


# def prc_submit_successful(contract_id):
#     result = calls.c_submit_successful(ObjectId(contract_id), {
#         'event': 'successful: something about ratings being completed....',#HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#         'time': datetime.fromisoformat(datetime.utcnow().isoformat()[:-7])
#     })
#     if result.acknowledged:
#         return True
#     return False

#need to have front end take care of time difference between server and user
def prep_graph(phase, timeline_arr, type_contract, tz_offset):
    print(datetime.utcnow())
    print(datetime.now())
    print(datetime.now() + timedelta(minutes=int(tz_offset)))
    months_arr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    skip_stall_arr = ['approved', 'asubmission', 'inprogress', 'rating', 'successful', 'validation']
    now_time = user_time = datetime.utcnow()
    if tz_offset != 'none':
        tz_offset = int(tz_offset)
        user_time = user_time - timedelta(minutes=tz_offset)
    else:
        tz_offset = 0
    teh_graph = {}
    counter = 0
    now_written = False
    last_date = timeline_arr[0]['time'] - timedelta(minutes=tz_offset)
    for obj in timeline_arr:
        if obj['time']:
            # only show stall in 'creation' and 'open' contracts
            if counter == 2 and phase in skip_stall_arr:
                pass
            else:
                if not now_written and (obj['time'] - timedelta(minutes=tz_offset)) > last_date and user_time < (
                        obj['time'] - timedelta(minutes=tz_offset)):
                    if user_time.date() in teh_graph.keys():
                        teh_graph[user_time.date()].append({user_time.time(): 'your last visit'})
                        now_written = True
                    else:
                        teh_graph[user_time.date()] = [{user_time.time(): 'your last visit'}]
                        now_written = True
                if (obj['time'] - timedelta(minutes=tz_offset)).date() in teh_graph.keys():
                    teh_graph[(obj['time'] - timedelta(minutes=tz_offset))].append( {(obj['time'] - timedelta(minutes=tz_offset)): obj['event']} )
                else:
                    teh_graph[(obj['time'] - timedelta(minutes=tz_offset))] = [
                        {(obj['time'] - timedelta(minutes=tz_offset)): obj['event']}]
                last_date = obj['time'] - timedelta(minutes=tz_offset)
        counter += 1
    # for obj in timeline_arr:
    #     if obj['time']:
    #         # only show stall in 'creation' and 'open' contracts
    #         if counter == 2 and phase in skip_stall_arr:
    #             pass
    #         else:
    #             if not now_written and (obj['time'] - timedelta(minutes=tz_offset)) > last_date and user_time < (obj['time'] - timedelta(minutes=tz_offset)):
    #                 if str(user_time.date()) in teh_graph.keys():
    #                     teh_graph[str(user_time.date())].append({str(user_time.time()): 'your last visit'})
    #                     now_written = True
    #                 else:
    #                     teh_graph[str(user_time.date())] = [{str(user_time.time()): 'your last visit'}]
    #                     now_written = True
    #             if str((obj['time'] - timedelta(minutes=tz_offset)).date()) in teh_graph.keys():
    #                 teh_graph[str((obj['time'] - timedelta(minutes=tz_offset)).date())].append({str((obj['time'] - timedelta(minutes=tz_offset)).time()): obj['event']})
    #             else:
    #                 teh_graph[str((obj['time'] - timedelta(minutes=tz_offset)).date())] = [{str((obj['time'] - timedelta(minutes=tz_offset)).time()): obj['event']}]
    #             last_date = obj['time'] - timedelta(minutes=tz_offset)
    #     counter += 1
    if not now_written:
        teh_graph[str(now_time.date())] = [{str(user_time.time()): 'your last visit'}]
    return teh_graph

# returns User array, False
def process_email_token(email_token):
    doc_or_false = calls.get_active_token(email_token)
    # does unhashed token match email saved in user record?
    email = URLSafeTimedSerializer(urlsafetimedserializer).loads(email_token, salt=urlsafetimedserializersalt)
    if doc_or_false:
        doc_or_false = calls.delete_active_token(email_token)
        print(doc_or_false)
        doc_or_false['dateused'] = datetime.utcnow()
        insert_one_result = calls.set_used_token(doc_or_false)
        print(doc_or_false)
        doc_or_none = calls.set_emailconfirmed(email, {'event': 'user activated account via email registration link',
                                                       'time': datetime.utcnow()}, doc_or_false['userid'])
        print(doc_or_none)
        # send thank you email...
        return [str(doc_or_none['_id']), doc_or_none['email'], doc_or_none['uName'], doc_or_none['_id'],
                doc_or_none['tz_offset']]
        #user_arr = calls.get_auth_user(email, password1, tz_offset)
        # login_user(User(user_arr[0], user_arr[1], user_arr[2], user_arr[3], user_arr[4]))
        # next = flask.request.args.get('next')
        # if not is_safe_url(next):
        #     return flask.abort(400)
    doc_or_false = calls.get_expired_token(email_token)
    if doc_or_false:
        return 'expired'
    doc_or_false = calls.get_used_token(email_token)
    if doc_or_false:
        return 'used'
    calls.set_strange_token(datetime.utcnow(), email_token)
    return False


'''
INCOMPLETE: 
NEED TO VERIFY ALL INPUT HERE BEFORE SENDING TO CALLS
good return = array of validated form data
'''

# need to adjust for user's timezone
def process_new_contract(form_dict, owner_id, owner_uname, tz_offset):
    # handle a malformed dictionary...
    now_time = user_time = datetime.utcnow()
    if tz_offset != 'none':
        tz_offset = int(tz_offset)
        user_time = user_time - timedelta(minutes=tz_offset)
        print(user_time)
    else:
        tz_offset = 0
    user_obj = {}
    bounty = float(form_dict['c_f_bounty'])
    user_obj.update({'bounty': bounty})
    user_obj.update({'bhunter': None})
    e_f_bonus = float(form_dict['c_f_efbonus'])
    user_obj.update({'efbonus': float(e_f_bonus)})
    e_g_bonus = float(form_dict['c_f_egbonus'])
    user_obj.update({'egbonus': float(e_g_bonus)})
    lostudy = form_dict['c_f_lostudy']
    user_obj.update({'lostudy': lostudy})
    specialization = form_dict['c_f_specialization']
    user_obj.update({'specialization': specialization})
    stall_iso = datetime.fromisoformat(form_dict['c_f_t_stall'] + 'T' + form_dict['c_f_t_s_time'] + ':00+00:00') + timedelta(minutes=tz_offset)
    start_iso = pytz.utc.localize(datetime.utcnow())
    user_obj.update({'clog': []})
    subject = form_dict['c_f_subject']
    user_obj.update({'subject': subject})
    type_contract = form_dict['c_f_type']
    user_obj.update({'type_contract': type_contract})
    instructions = form_dict['c_f_instructions']
    user_obj.update({'instructions': instructions})
    # set up assignment contract:
    if type_contract == 'assignment':
        a_deadline_iso = datetime.fromisoformat(form_dict['c_f_t_a_deadline'] + 'T' + form_dict['c_f_t_a_d_time'] + ':00+00:00') + timedelta(minutes=tz_offset)
        efbonus_deadline = form_dict['c_f_efb_deadline']
        if e_f_bonus > 0 and efbonus_deadline != '':
            efbonus_deadline = datetime.fromisoformat(form_dict['c_f_efb_deadline'] + 'T' + form_dict['c_f_efb_d_time'] + ':00+00:00') + timedelta(minutes=tz_offset)
        else:
            efbonus_deadline = None
        rating_deadline = None
        g_deadline = None
        if e_g_bonus > 0 or form_dict['grade_wait_yon'] == 'true':
            g_deadline = a_deadline_iso + timedelta(days=7)
            rating_deadline = g_deadline + timedelta(days=7)
        else:
            rating_deadline = a_deadline_iso + timedelta(days=7)
        user_obj.update({'timeline': [{'time': start_iso, 'event': 'created'},
                                      {'time': None, 'event': 'contract set inprogress'},
                                      {'time': stall_iso, 'event': 'stall deadline'},
                                      {'time': efbonus_deadline, 'event': 'early finish bonus deadline'},
                                      {'time': a_deadline_iso, 'event': 'assignment submission deadline'},
                                      {'time': g_deadline, 'event': 'grade submission deadline'},
                                      {'time': rating_deadline, 'event': 'rate user deadline'}]})
    # set up test contract:
    if type_contract == 'test':
        t_start_iso = datetime.fromisoformat(form_dict['c_f_t_t_start'] + 'T' + form_dict['c_f_t_t_s_time'] + ':00+00:00') + timedelta(minutes=tz_offset)
        t_end_iso = datetime.fromisoformat(form_dict['c_f_t_t_end'] + 'T' + form_dict['c_f_t_t_e_time'] + ':00+00:00') + timedelta(minutes=tz_offset)
        g_deadline = None
        rating_deadline = None
        if e_g_bonus > 0 or form_dict['grade_wait_yon'] == 'true':
            g_deadline = t_end_iso + timedelta(days=7)
            rating_deadline = g_deadline + timedelta(days=7)
            print(type(rating_deadline))
        else:
            rating_deadline = t_end_iso + timedelta(days=7)
        user_obj.update({'timeline': [{'time': start_iso, 'event': 'created'},
                                      {'time': None, 'event': 'contract set inprogress'},
                                      {'time': stall_iso, 'event': 'stall deadline'},
                                      {'time': t_start_iso, 'event': 'test starts'},
                                      {'time': t_end_iso, 'event': 'test ends'},
                                      {'time': g_deadline, 'event': 'grade submission deadline'},
                                      {'time': rating_deadline, 'event': 'rate user deadline'}]})
    # add in data not initiated by user:
    user_obj.update({'owner': owner_id})
    user_obj.update({'iparties': []})
    user_obj.update({'clog': [{'event': 'created', 'time': start_iso}]})
    user_obj.update({'phase': 'creation'})
    user_obj.update({'reviews': []})
    user_obj.update({'chat': []})
    user_obj.update({'lvbhunter': None})
    user_obj.update({'lvowner': None})
    user_obj.update({'sampleUp': None})
    user_obj.update({'asubmission': None})
    user_obj.update({'gsubmission': None})
    user_obj.update({'chatnewmsgbhunter': False})
    user_obj.update({'chatnewmsgowner': False})
    user_obj.update({'paymentid': None})
    user_obj.update({'bhunter_uname': None})
    user_obj.update({'owner_uname': owner_uname})
    if float(e_f_bonus) <= 0.0:
        user_obj.update({'efbonusyon': False})
    else:
        user_obj.update({'efbonusyon': True})
    if e_g_bonus <= 0.0:
        user_obj.update({'egbonusyon': False})
    else:
        user_obj.update({'egbonusyon': True})
    return calls.create_contract(user_obj)

# notdone
# returns True if ???
# returns False if ???
def process_new_user(email, mail, password1, tz_offset, username):
    user_template = {
        'active': True,
        'email': email,
        'emailconfirmed': False,
        'joinDate': datetime.utcnow(),
        'pass': generate_password_hash(password1),
        'paymentid': None,
        'reviewHistory': [],
        'tz_offset': tz_offset,
        'uName': username,
        'userlog': [{'event': 'user created their account and must confirm registration email',
                     'time': datetime.utcnow()}]
    }
    insert_one_result = calls.create_user(user_template)
    if insert_one_result.acknowledged:
        email_token = URLSafeTimedSerializer(urlsafetimedserializer).dumps(email, salt=urlsafetimedserializersalt)
        # store email_token in database:
        is_token_stored = calls.set_activetoken({
            'dateactive': datetime.utcnow(),
            #'expiredate': datetime.utcnow() + timedelta(days=3),
            'expiredate': datetime.utcnow(),
            'dateused': None,
            'token': email_token,
            'userid': insert_one_result.inserted_id
        })
        message = Message('confirm la email', sender='listen_silent@hotmail.com', recipients=[email])
        link = url_for('confirm_email', email_token=email_token, _external=True)
        print(link)
        message.body = 'Your link is ' + link
        mail.send(message)
        return True
    return False


def process_user_orders(userid_obj):
    cursor_obj = calls.get_user_contracts(userid_obj)
    if cursor_obj:
        obj_arr = []
        for doc in cursor_obj:
            obj_arr.append(doc)
        return obj_arr
    else:
        return None


if __name__ == '__main__':
    print(get_user_record_l('theman@gmail.com', 'passwordpass'))