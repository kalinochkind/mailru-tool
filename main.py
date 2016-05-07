#!/usr/bin/python3

import urllib.request
import urllib.parse
import json
import webbrowser
from http.cookiejar import CookieJar
import re
import sys

N = 100

def cookieByName(cj, name):
    for i in cj:
        if i.name == name:
            return i.value

class MailruParser:
    def __init__(self, login=None, password=None):
        cj = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        self.token = None
        self.salt = None
        if login:
            self.opener.open('https://auth.mail.ru/cgi-bin/auth', urllib.parse.urlencode({'Login': login+'@mail.ru', 'Username': login, 'Password': password}).encode('utf-8'))
            page = self.opener.open('https://otvet.mail.ru/?login=1').read().decode('utf-8') # token in 'ot' cookie
            self.token = cookieByName(cj, 'ot')
            try:
                self.salt = re.search(r'"salt" : "([a-zA-Z0-9]+)",', page).group(1)
            except AttributeError:
                self.salt = None
            if self.token:
                print('Authorization successful')
            else:
                print('Authorization failed')
                sys.exit()

    def apiCall(self, name, params):
        if self.token:
            params.update({'token': self.token, 'salt': self.salt})
        url = 'https://otvet.mail.ru/api/v2/' + name + '?' + urllib.parse.urlencode(params)
        return json.loads(urllib.request.urlopen(url).read().decode())


    def readPage(self, p, state):
        data = self.apiCall('questlist', {'n': N, 'p': p, 'state': state})
        return data['qst']

    def readQuestion(self, qid):
        return self.apiCall('question', {'qid': qid})

    def canVote(self, qid):
        return self.readQuestion(qid).get('canreply')

    def enumQuestions(self, state):
        p = 0
        while True:
            for i in self.readPage(p, state):
                yield i
            p += N

    def enumPolls(self):
        for i in self.enumQuestions('A'):
            if i.get('polltype') == 'S' and self.canVote(i['id']):
                yield i['id']

    def enumVoting(self):
        for i in self.enumQuestions('V'):
            if self.canVote(i['id']):
                yield i['id']


def main():
    s = set()
    try:
        login, password = open('login.txt').read().splitlines()
        m = MailruParser(login, password)
    except Exception:
        login = input('Username: ')
        password = input('Password: ')
        m = MailruParser(login, password)
        with open('login.txt', 'w') as f:
            f.write(login + '\n' + password)
    mode = input('Mode (p/v): ').lower()
    while mode not in 'pv':
        mode = input('Mode (p/v): ').lower()
    for i in (m.enumPolls() if mode == 'p' else m.enumVoting()):
        if i in s:
            continue
        s.add(i)
        i = 'https://otvet.mail.ru/question/' + str(i)
        print(i, end='')
        webbrowser.open(i)
        input()

if __name__ == '__main__':
    main()
