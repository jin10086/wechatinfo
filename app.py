from flask import Flask, render_template
from pyecharts.constants import DEFAULT_HOST
import itchat, time, sys
from collections import Counter
from pyecharts import WordCloud, Pie, Map
import pickle
import jieba.analyse

app = Flask(__name__)


@app.route('/')
def index():
    friends, chatrooms, mps = pickleload()
    province_map = province_chart(friends)
    gender_pie = gender_chart(friends)
    sig_wordcloud = signature_chart(friends)

    return render_template('pyecharts.html',
                           myechart=get_chart_list([province_map,gender_pie,sig_wordcloud]),
                           host=DEFAULT_HOST,
                           script_list=get_js_list([province_map,gender_pie,sig_wordcloud]))


# 测试的时候用
def pickleload():
    with open('1.pk', 'rb') as f:
        friends, chatrooms, mps = pickle.load(f)
        return friends, chatrooms, mps


# TODO: 在网页上实时显示登陆状态
def login():
    '登录微信网页版'
    uuid = open_QR()
    waitForConfirm = False
    while 1:
        status = itchat.check_login(uuid)
        if status == '200':
            break
        elif status == '201':
            if waitForConfirm:
                output_info('Please press confirm')
                waitForConfirm = True
        elif status == '408':
            output_info('Reloading QR Code')
            uuid = open_QR()
            waitForConfirm = False
    userInfo = itchat.web_init()
    friends = itchat.get_friends(True)
    chatrooms = itchat.get_chatrooms()
    mps = itchat.get_mps()
    # 测试的时候用
    with open('1.pk', 'wb') as f:
        pickle.dump([friends, chatrooms, mps], f)

    return friends, chatrooms, mps


# TODO:  把二维码在网页上展示
def open_QR():
    for get_count in range(10):
        output_info('Getting uuid')
        uuid = itchat.get_QRuuid()
        while uuid is None: uuid = itchat.get_QRuuid();time.sleep(1)
        output_info('Getting QR Code')
        if itchat.get_QR(uuid):
            break
        elif get_count >= 9:
            output_info('Failed to get QR Code, please restart the program')
            sys.exit()
    output_info('Please scan the QR Code')
    return uuid


def province_chart(friends):
    '绘制地区分布图'
    province = [i['Province'] for i in friends]
    attr, value = x(province)
    map = Map("好友地理位置分布", width=1200, height=600)
    map.add("", attr, value, is_visualmap=True, visual_text_color='#000')
    return map


def gender_chart(friends):
    '绘制性别饼图'
    gender = [i['Sex'] for i in friends]
    intToSex = {"0": "未知",
                "1": "男",
                "2": "女"}
    attr, vv = [], []
    for k, v in Counter(gender).items():
        attr.append(intToSex[str(k)])
        vv.append(str(v))
    pie = Pie("好友性别分布",width=1200, height=600)
    pie.add("", attr, vv, is_label_show=True)
    return pie

def signature_chart(friends):
    '绘制个性签名词云'
    sig = '。'.join([i['Signature'] for i in friends])
    sig_textrank = jieba.analyse.textrank(sig, withWeight=True, topK=30)
    name,value = [],[]
    for k, v in dict(sig_textrank).items():
        name.append(k)
        value.append(str(v))
    wordcloud = WordCloud(width=1200, height=600)
    wordcloud.add("", name, value, word_size_range=[20, 100])
    return wordcloud


def output_info(msg):
    print('[INFO] %s' % msg)


def x(val):
    a, b = [], []
    for k, v in Counter(val).items():
        a.append(str(k))
        b.append(str(v))
    return a, b

def get_js_list(x):
    script_list = []
    for i in x:
        script_list.extend(i.get_js_dependencies())
    _ = list(set(script_list))
    _.remove('echarts.min')
    return ['echarts.min'] + _

def get_chart_list(x):
    return [i.render_embed() for i in x]

if __name__ == '__main__':
    app.run(debug=True)
