from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from io import BytesIO
import time
import requests
import demjson
import re
import datetime
import getpass


qq = ''
pwd = ''


def print_time():
    print(datetime.datetime.now(), end=' ')


def get_gtk(p_skey):
    hash=5381
    for i in p_skey:
        hash += (hash << 5)+ord(i)

    print_time()
    print('生成gtk')
    return hash & 0x7fffffff


def change_cookie(cookie):
    s = ''
    for c in cookie:
        s = s + c['name'] + '=' + c['value'] + '; '

    return s


def check_time():
    now = datetime.datetime.now()
    hour = str(now)[11:13]
    minute = str(now)[14:16]
    second = str(now)[17:19]

    if 0 == int(hour) % 6 and minute == '00' and int(second) < 30:
        return True
    else:
        return False


def get_image_difference(back_img, full_img):
    width, height = full_img.size

    for w in range(0, width):
        for h in range(0, height):
            back_pixel = back_img.getpixel((w, h))
            full_pixel = full_img.getpixel((w, h))

            if back_pixel != full_pixel and w > 340 and h > 10 and abs(back_pixel[0]-full_pixel[0])>50 and abs(back_pixel[1]-full_pixel[1])>50 and abs(back_pixel[2]-full_pixel[2])>50:
                return True, w

    return False, -1


def get_cookie():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=chrome_options)

    driver.get('https://qzone.qq.com/')

    driver.switch_to.frame('login_frame')

    driver.find_element_by_id('switcher_plogin').click()
    driver.find_element_by_id('u').clear()
    driver.find_element_by_id('u').send_keys(qq)
    driver.find_element_by_id('p').clear()
    driver.find_element_by_id('p').send_keys(pwd)
    driver.find_element_by_id('login_button').click()

    time.sleep(3)
    frame = driver.find_element_by_xpath('//*[@id="newVcodeIframe"]/iframe')
    driver.switch_to.frame(frame)

    #
    back_url = driver.find_element_by_id('slideBkg').get_attribute('src')
    full_url = back_url.replace('hycdn_1', 'hycdn_0')

    r = requests.get(back_url)
    file = BytesIO(r.content)
    back_img = Image.open(file)

    r.status_code = 500
    while 200 != r.status_code:
        r = requests.get(full_url)

    file = BytesIO(r.content)
    full_img = Image.open(file)

    r, w = get_image_difference(back_img, full_img)
    if r is False:
        return

    # print(w)
    # 280 * 158
    # 680 * 390
    # 55 * 55
    # 136 * 136
    # 214

    slide = driver.find_element_by_id('tcaptcha_drag_thumb')
    ActionChains(driver).click_and_hold(slide).perform()
    ActionChains(driver).move_by_offset(xoffset=w / 680 * 250, yoffset=0).perform()
    ActionChains(driver).release(slide).perform()

    # print(back_img.size)
    # print(cut_img.size)
    # print(full_img.size)

    time.sleep(2)

    driver.find_element_by_id('QZ_Body').click()

    cookie = driver.get_cookies()

    # print(cookie)

    driver.close()
    driver.quit()

    print_time()
    print('提取cookie')

    return cookie


def get_args():
    cookie = get_cookie()

    for c in cookie:
        if c['name'] == 'p_skey':
            p_skey = c['value']
            break

    cookie = change_cookie(cookie)

    # print(p_skey)

    gtk = get_gtk(p_skey)

    return cookie, gtk


def do_like(d, gtk, headers):
    url = 'https://user.qzone.qq.com/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app?g_tk=' + str(gtk)

    body = {
        'qzreferrer': 'http://user.qzone.qq.com/' + qq,
        'opuin': qq,
        'from': 1,
        'active': 0,
        'fupdate': 1
    }

    try:
        html = d['html']

        # print(html)
        # unikey = re.search(r'data-unikey=\"http:[^"]*\"', html).group(0)
        # curkey = re.search(r'data-curkey=\"http:[^"]*\"', html).group(0)
        # print(unikey, curkey)

        temp = re.search('data-unikey="(http[^"]*)"[^d]*data-curkey="([^"]*)"[^d]*data-clicklog=("like")[^h]*href="javascript:;"', html);

        if temp is None:
            return

        unikey = temp.group(1);
        curkey = temp.group(2);

        # print(unikey, curkey)

        body['unikey'] = unikey
        body['curkey'] = curkey
        body['appid'] = d['appid']
        body['typeid'] = d['typeid']
        body['fid'] = d['key']

        r = requests.post(url, data=body, headers=headers)

        if 200 == r.status_code:
            print_time()
            print('给 ' +  d['nickname'] + ' 点赞')

    except:
        return


def get_content(headers, gtk):

    try:
        r = requests.get('http://ic2.s8.qzone.qq.com/cgi-bin/feeds/feeds3_html_more?uin=0924761163&scope=0&view=1&daylist=&uinlist=&gid=&flag=1&filter=all&applist=all&refresh=0&aisortEndTime=0&aisortOffset=0&getAisort=0&aisortBeginTime=0&pagenum=1&externparam=offset%3D6%26total%3D97%26basetime%3D1470323193%26feedsource%3D0&firstGetGroup=0&icServerTime=0&mixnocache=0&scene=0&begintime=0&count=10&dayspac=0&sidomain=cnc.qzonestyle.gtimg.cn&useutf8=1&outputhtmlfeed=1&getob=1&g_tk=' + str(gtk), headers=headers)

        r = r.text[10:-2]

        r = demjson.decode(r)

        data = r['data']['data']

        print_time()
        print('获取了 ' + str(len(data)) + ' 条说说')

        return data
    except:
        return []


def main():

    print_time()
    print('程序运行...')

    global qq
    global pwd

    qq = input('QQ:')
    pwd = getpass.getpass('Password:')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
    }

    cookie, gtk = get_args()
    headers['Cookie'] = cookie

    while True:
        time.sleep(1)

        if check_time():
            cookie, gtk = get_args()
            headers['Cookie'] = cookie

            print_time()
            print('更新了 cookie 和 gtk')

        data = get_content(headers, gtk)

        for d in data:
            do_like(d, gtk, headers)


if __name__ == '__main__':
    main()
