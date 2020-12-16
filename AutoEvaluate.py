import io
import json
import msvcrt
import os
import re
from hashlib import md5

import requests
from PIL import Image


def psd_input(text):
    chars = []
    print('', end='\r' + text)
    while True:
        try:
            newChar = msvcrt.getch().decode(encoding="utf-8")
        except:
            return input("\n(您可能输入了非法字符,密码输入将不能被隐藏,请重新输入：)")
        if newChar in '\r\n':
            break
        elif newChar == '\b':
            if chars:
                del chars[-1]
                msvcrt.putch('\b'.encode(encoding='utf-8'))
                msvcrt.putch(' '.encode(encoding='utf-8'))
                msvcrt.putch('\b'.encode(encoding='utf-8'))
        else:
            chars.append(newChar)
            msvcrt.putch('*'.encode(encoding='utf-8'))
    return (''.join(chars))


print("*********************欢迎您使用自动评教系统*********************\n")
version = 'v2.3 (2020.12.14)'
print('Version: ' + version)
print('Coder: JieYijian')
print('本程序可自动完成吉林大学学生的教学质量评价。')
print('本程序仅供学习和研究使用，不得用于商业用途！')
print('本程序已开源，github地址：https://github.com/EugeneJie/AutoEvaluate')
print('如果您在使用过程中遇到问题，可联系作者邮箱：jieyijian@yeah.net')
print('\n-----------------------------------------------------------------')
s = requests.session()

username = input('\n请输入您的教学号：')
password = psd_input('请输入您的密码：')

headers = {'Content-Type': 'application/json'}

print('\n\n正在获取验证码...')

j_password = md5(('UIMS' + username + password).encode()).hexdigest()
a = s.get("https://uims.jlu.edu.cn/ntms/open/get-captcha-image.do?s=1").content
byte_stream = io.BytesIO(a)
im = Image.open(byte_stream)
im.show()
vcode = input("验证码：")
cookies = {
    'loginPage': 'userLogin.jsp',
    'alu': username
}
requests.utils.add_dict_to_cookiejar(s.cookies, cookies)

post_data = {
    'username': username,
    'password': j_password,
    'mousePath': '',
    'vcode': vcode
}
r = s.post('http://uims.jlu.edu.cn/ntms/j_spring_security_check', data=post_data)

message = re.findall('<span class="error_message" id="error_message">(.*?)</span>', r.text)
if message:
    print(message[0])

r = s.post('http://uims.jlu.edu.cn/ntms/action/getCurrentUserInfo.do')
info = json.loads(r.text)
name = info['loginInfo']['nickName']
t = info['groupsInfo'][0]['groupName']

if info['userType'] == 'S' or t == '学生':
    t = '同学'

if t == '同学':
    print("登录成功！欢迎您：" + name + " " + t + '！\n')
else:
    print("您好，" + name + ' ' + t + '！系统检测到您可能不是学生，无法进行教学质量评价，感谢您的支持！\n')

post_url = 'http://uims.jlu.edu.cn/ntms/service/res.do'

defRes = info['defRes']
schId = defRes['school']
deptId = defRes['department']
adcId = defRes['adcId']

classmate_list = []
post_data = {
    "tag": "student_sch_dept",
    "branch": "default",
    "params": {"schId": "%s" % schId,
               "deptId": "%s" % deptId,
               "adcId": "%s" % adcId}
}
r = s.post(post_url, data=json.dumps(post_data), headers=headers)
classmate_info = json.loads(r.text)['value']
for classmate in classmate_info:
    classmate_list.append(classmate['name'])

print('正在查询可评课程...')
post_data = {
    "tag": "student@evalItem",
    "branch": "self",
    "params": {"blank": "Y"}
}

r = s.post('http://uims.jlu.edu.cn/ntms/service/res.do', data=json.dumps(post_data), headers=headers)
eval_info = json.loads(r.text)['value']
num = len(eval_info)
if num == 0:
    post_data = {
        "tag": "student@evalItem",
        "branch": "self",
        "params": {"done": "Y"}
    }
    r = s.post('http://uims.jlu.edu.cn/ntms/service/res.do', data=json.dumps(post_data), headers=headers)
    finish_info = json.loads(r.text)['value']
    if len(finish_info) == 0:
        print('当前可能并非教学质量评价时段，没有可评价的课程！\n')
        print('感谢您的使用！\n')
        os.system('pause')
        exit()
    else:
        print('您已完成所有 %d 条评价项，无需进行评教！\n' % len(finish_info))
        print('感谢您的使用！\n')
        os.system('pause')
        exit()
else:
    print('您还有 %d 条未完成的评价\n' % num)

print('正在进行教学质量评价...\n')
count = 0
puzzle = ''
for course in eval_info:
    id = course['evalItemId']
    post_data = {"evalItemId": "%s" % id}
    post_url = 'https://uims.jlu.edu.cn/ntms/action/eval/fetch-eval-item.do'
    r = s.post(post_url, data=json.dumps(post_data), headers=headers)
    puzzle_info = json.loads(r.text)['items'][0]['puzzle']
    flag = False

    for classmate in classmate_list:
        length = len(puzzle_info) if len(puzzle_info) < len(classmate) else len(classmate)
        for i in range(length):
            if puzzle_info[i] == '_':
                puzzle = classmate[i]
                cl_name = puzzle_info.replace('_', puzzle)

        if cl_name == classmate:
            flag = True
            break

    # 一般情况下均可获取到班级同学信息，可去掉 #
    if not flag:
        puzzle = input('请输入在下划线处对应的一个汉字，以构成一个你们班级同学的名字（%s）：' % puzzle_info)
        classmate_list.append(puzzle_info.replace('_', puzzle))
    ###

    post_url = 'http://uims.jlu.edu.cn/ntms/action/eval/eval-with-answer.do'
    post_data = {"guidelineId": 160, "evalItemId": "%s" % id,
                 "answers": {"p01": "A", "p02": "A", "p03": "A", "p04": "A",
                             "p05": "A", "p06": "A", "p07": "A", "p08": "A", "p09": "A",
                             "p10": "A", "sat11": "A", "sat12": "A", "puzzle_answer": "%s" % puzzle},
                 "clicks": {"_boot_": 0, "p01": 49050, "p02": 50509,
                            "p03": 52769, "p04": 54833, "p05": 58783,
                            "p06": 61488, "p07": 62599,
                            "p08": 64182, "p09": 68422, "p10": 70505,
                            "sat11": 71589, "sat12": 73270}}
    s.post(post_url, data=json.dumps(post_data), headers=headers)
    count += 1
    print(str(count) + ' - ' + course['target']['name'] + ' 老师的 ' + course['targetClar']['notes'][2:] + ' 评价完成！\n')

print('教学质量评价已完成！')
print('\n\n感谢您的使用！\n\n')
os.system('pause')
