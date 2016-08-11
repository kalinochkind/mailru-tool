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
            self.opener.open('https://auth.mail.ru/cgi-bin/auth', urllib.parse.urlencode({'Login': login, 'Username': login, 'Password': password}).encode('utf-8'))
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

    def apiCall(self, name, params, method='get'):
        if self.token:
            params.update({'token': self.token, 'salt': self.salt})
        if method.lower() == 'get':
            url = 'https://otvet.mail.ru/api/v2/' + name + '?' + urllib.parse.urlencode(params)
            return json.loads(self.opener.open(url).read().decode())
        else:
            url = 'https://otvet.mail.ru/api/v2/' + name
            return json.loads(self.opener.open(url, urllib.parse.urlencode(params).encode('utf-8')).read().decode())

    def readPage(self, p, state):
        data = self.apiCall('questlist', {'n': N, 'p': p, 'state': state})
        return data['qst']

    def readQuestion(self, qid):
        return self.apiCall('question', {'qid': qid})

    def enumQuestions(self, state):
        p = 0
        while True:
            for i in self.readPage(p, state):
                yield i
            p += N

    def enumPolls(self):
        print('Polls')
        cnt = 0
        for i in self.enumQuestions('A'):
            if i.get('polltype') == 'S':
                q = self.readQuestion(i['id'])
                if q.get('canreply'):
                    resp = self.apiCall('votepoll', {'qid': i['id'], 'vote[]': q['poll']['options'][0]['optid']}, method='post')
                    if resp.get('errid') == 222:
                        print('Limit reached, {} done'.format(cnt))
                        return
                    cnt += 1
                    print('https://otvet.mail.ru/question/' + str(i['id']))

    def enumVoting(self):
        print('Voting')
        cnt = 0
        for i in self.enumQuestions('V'):
            q = self.readQuestion(i['id'])
            if q.get('canreply'):
                resp = self.apiCall('votefor', {'qid': i['id'], 'aid': q['answers'][0]['id']}, method='post')
                if resp.get('errid') == 223:
                    print('Limit reached, {} done'.format(cnt))
                    return
                cnt += 1
                print('https://otvet.mail.ru/question/' + str(i['id']))

def main():
    try:
        lines = [i for i in open('login.txt').read().strip().splitlines() if i.strip() and not i.startswith('#')]
    except FileNotFoundError:
        print('login.txt does not exist')
        return
    if not lines:
        print('No accounts found')
        return
    for line in lines:
        try:
            login, password = line.split(maxsplit=1)
            if '@' not in login:
                login += '@mail.ru'
            print('Using account', login)
            m = MailruParser(login, password)
            if m.token:
                m.enumPolls()
                m.enumVoting()
            print()
        except Exception:
            pass


if __name__ == '__main__':
    main()
