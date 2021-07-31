from django.contrib.auth.hashers import BasePasswordHasher, MD5PasswordHasher, mask_hash
from django.contrib import auth
from django.conf import settings
from boottest import local_dict

from datetime import datetime, timedelta
import hashlib
import re


class MyMD5PasswordHasher(MD5PasswordHasher):
    algorithm = "mymd5"
    salt = ""

    def __init__(self, salt):
        self.salt = salt

    def encode(self, password):
        assert password is not None
        password = (password + self.salt).encode("utf-8")
        hash = hashlib.md5(password).hexdigest().upper()
        return hash

    def verify(self, password, encoded):
        encoded_2 = self.encode(password)
        return encoded.upper() == encoded_2.upper()


class MySHA256Hasher(object):
    def __init__(self, secret):
        self.secret = secret

    def encode(self, identifier):
        assert identifier is not None
        identifier = (identifier + self.secret).encode("utf-8")
        return hashlib.sha256(identifier).hexdigest().upper()

    def verify(self, identifier, encoded):
        encoded_2 = self.encode(identifier)
        return encoded.upper() == encoded_2.upper()


from app.models import NaturalPerson, Organization, Position


def check_user_type(user):  # return Valid(Bool), otype
    html_display = {}
    if user.is_superuser:
        return False, "", html_display
    if user.username[:2] == "zz":
        user_type = "Organization"
        html_display["profile_name"] = "组织主页"
        html_display["profile_url"] = "/orginfo/"
        org = Organization.objects.get(organization_id=user)
        html_display["avatar_path"] = get_user_ava(org, user_type)
        html_display['user_type'] = user_type
    else:
        user_type = "Person"
        person = NaturalPerson.objects.activated().get(person_id=user)
        html_display["profile_name"] = "个人主页"
        html_display["profile_url"] = "/stuinfo/"
        html_display["avatar_path"] = get_user_ava(person, user_type)
        html_display['user_type'] = user_type

    return True, user_type, html_display


def get_user_ava(obj, user_type):
    try:
        ava = obj.avatar
        assert ava != ""
        return settings.MEDIA_URL + str(ava)
    except:
        if user_type == "Person":
            return settings.MEDIA_URL + "avatar/person_default.jpg"
        else:
            return settings.MEDIA_URL + "avatar/org_default.png"


def get_user_left_narbar(
        person, is_myself, html_display
):  # 获取左边栏的内容，is_myself表示是否是自己, person表示看的人
    assert (
            "is_myself" in html_display.keys()
    ), "Forget to tell the website whether this is the user itself!"
    html_display["underground_url"] = local_dict["url"]["base_url"]

    my_org_id_list = Position.objects.activated().filter(person=person).filter(pos=0)
    html_display["my_org_list"] = [w.org for w in my_org_id_list]  # 我管理的组织
    html_display["my_org_len"] = len(html_display["my_org_list"])
    return html_display


def get_org_left_narbar(org, is_myself, html_display):
    assert (
            "is_myself" in html_display.keys()
    ), "Forget to tell the website whether this is the user itself!"
    html_display["switch_org_name"] = org.oname
    html_display["underground_url"] = local_dict["url"]["base_url"]
    html_display['org'] = org
    return html_display


# 检查发起活动的request的合法性
def check_ac_request(request):
    # oid的获取
    context = dict()
    context['warn_code'] = 0
    # signup_start = request.POST["actstar"]
    act_start = request.POST.get("actstart")  # 活动报名时间
    act_end = request.POST.get("actend")  # 活动报名结束时间
    prepare_scheme = request.POST.get("prepare_scheme")
    try:
        prepare_scheme = int(prepare_scheme)
        prepare_times = [1, 24, 72, 168]
        prepare_time = prepare_times[prepare_scheme]
    except:
        context['warn_code'] = 10
        context['warn_msg'] = "Unexpected exception. If you are not doing it deliberately, please contact the administrator to report this bug."
        return context

    capacity = 0
    schema = 0  # 投点模式，默认0为先到先得
    URL = ""
    try:
        t = int(request.POST["unlimited_capacity"])
        capacity = -1
    except:
        capacity = 0
    try:
        if capacity == 0:
            capacity = int(request.POST["maxpeople"])
        elif capacity == -1:
            capacity = 10000
        if capacity <= 0:
            context['warn_code'] = 1
            context['warn_msg'] = "The number of participants must exceed 0"
    except:
        context['warn_code'] = 2
        context['warn_msg'] = "The number of participants must be an integer"

    try:
        aprice = float(request.POST["aprice"])
        if aprice < 0:
            context['warn_code'] = 3
            context['warn_msg'] = "The price should be no less than 0!"
    except:
        context['warn_code'] = 4
        context['warn_msg'] = "The price must be a floating point number one decimal place"


    try:
        act_start = datetime.strptime(act_start, '%m/%d/%Y %H:%M %p')
        act_end = datetime.strptime(act_end, '%m/%d/%Y %H:%M %p')

        now_time = datetime.now()

        # 创建活动即开始报名
        signup_start = now_time
        signup_end = act_start - timedelta(hours=prepare_time)

        print('now', now_time)
        print('end', signup_end)

        if signup_start >= signup_end:
            context['warn_code'] = 7
            context['warn_msg'] = "No enough time to prepare."
            return context

        # 至少提前一小时发起活动，但上面的逻辑已经包含了
        '''
        if act_start < now_time + datetime.timedelta(hours=1):
            context['warn_code'] = 8
            context['warn_msg'] = "No enough time to prepare."
        '''
        if now_time + timedelta(days=30) < act_start == False:
            context['warn_code'] = 5
            context['warn_msg'] = "The activity has to be in a month! "


    except:
        context['warn_code'] = 6
        context['warn_msg'] = "you have sent a wrong time form!"



    try:
        URL = str(request.POST["URL"])
    except:
        URL = ""
    try:
        schema = int(request.POST["signschema"])
    except:
        schema = 0
    if context['warn_code'] != 0:
        return context

    context['aname'] = str(request.POST["aname"])  # 活动名称
    context['content'] = str(request.POST["content"])  # 活动内容
    context['location'] = str(request.POST["location"])  # 活动地点
    context['URL'] = str(request.POST["URL"])  # 活动推送链接
    context['capacity'] = capacity
    context['aprice'] = aprice  # 活动价格
    context['URL'] = URL
    context['signup_start'] = signup_start
    context['signup_end'] = signup_end
    context['act_start'] = act_start
    context['act_end'] = act_end
    context['prepare_scheme'] = prepare_scheme
    context['signschema'] = schema
    return context


# 时间合法性的检查，检查时间是否在当前时间的一个月以内，并且检查开始的时间是否早于结束的时间，
def check_ac_time(start_time, end_time):
    try:
        now_time = datetime.now().strptime('%Y-%m-%d %H:%M:%S')
        month_late = (now_time + datetime.timedelta(days=30))
        if now_time < start_time < end_time < month_late:
            return True  # 时间所处范围正确
    except:
        return False

    return False


def url_check(arg_url):
    if arg_url is None:
        return True
    for url in local_dict["url"].values():
        base = re.findall('^https?://[^/]*/?', url)[0]
        # print('base:', base)
        if re.match(base, arg_url):
            return True
    return False

# 允许进行 cross site 授权时，return True
def check_cross_site(request, arg_url):
    if arg_url is None:
        return True
    # 这里 base_url 最好可以改一下
    appointment = local_dict["url"]["base_url"]
    appointment_base = re.findall('^https?://[^/]*/', appointment)[0]
    if re.match(appointment_base, arg_url):
        valid, user_type, html_display = check_user_type(request)
        if not valid or user_type == "Organization":
            return False
    return True


def get_url_params(request,html_display):
    full_path = request.get_full_path()
    if "?" in full_path:
        params = full_path.split["?"][1]
        params = params.split['&']
        for param in params:
            key, value = param.split["="][0],param.split["="][1]
            if key not in html_display.keys():  #禁止覆盖
                html_display[key] = value
