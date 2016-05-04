#!/usr/bin/python3

import urllib.request
import json
import webbrowser

N = 100

def readPage(p):
    data = urllib.request.urlopen('https://otvet.mail.ru/api/v2/questlist?ajax_id=12&n={}&p={}'.format(N, p)).read().decode()
    return json.loads(data)['qst']

def enumQuestions():
    p = 0
    while True:
        for i in readPage(p):
            if i.get('polltype') == 'S':
                yield i['id']
        p += N


def main():
    s = set()
    for i in enumQuestions():
        if i in s:
            continue
        s.add(i)
        i = 'https://otvet.mail.ru/question/' + str(i)
        print(i, end='')
        webbrowser.open(i)
        input()

if __name__ == '__main__':
    main()
