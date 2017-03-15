import urllib.request
import urllib.parse
import json
from http.cookiejar import CookieJar
import re

class MailruParser:

    PAGE_SIZE = 100

    def __init__(self, login=None, password=None):
        if '@' not in login:
            login += '@mail.ru'
        cj = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        self.token = None
        self.salt = None
        self.answered_questions= set()
        if login:
            self.opener.open('https://auth.mail.ru/cgi-bin/auth', urllib.parse.urlencode({'Login': login, 'Username': login, 'Password': password}).encode('utf-8'))
            page = self.opener.open('https://otvet.mail.ru/?login=1').read().decode('utf-8') # token in 'ot' cookie
            self.token = self.cookieByName(cj, 'ot')
            try:
                self.salt = re.search(r'"salt" : "([a-zA-Z0-9]+)",', page).group(1)
            except AttributeError:
                self.salt = None
            if self.token:
                print('Authorization successful')
            else:
                print('Authorization failed')

    @staticmethod
    def cookieByName(cj, name):
        for i in cj:
            if i.name == name:
                return i.value

    def apiCall(self, name, params=None, method='get'):
        if params is None:
            params = {}
        if self.token:
            params.update({'token': self.token, 'salt': self.salt})
        if method.lower() == 'get':
            url = 'https://otvet.mail.ru/api/v2/' + name + '?' + urllib.parse.urlencode(params)
            return json.loads(self.opener.open(url).read().decode())
        else:
            url = 'https://otvet.mail.ru/api/v2/' + name
            return json.loads(self.opener.open(url, urllib.parse.urlencode(params).encode('utf-8')).read().decode())

    def readPage(self, p, state, count=0):
        data = self.apiCall('questlist', {'n': count or self.PAGE_SIZE, 'p': p, 'state': state})
        return data['qst']

    def readQuestion(self, qid):
        return self.apiCall('question', {'qid': qid})

    def enumQuestions(self, state):
        p = 0
        while True:
            for i in self.readPage(p, state):
                yield i
            p += self.PAGE_SIZE

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
                    if resp.get('errid') == 134:
                        print('Account is banned')
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
                if resp.get('errid') == 134:
                    print('Account is banned')
                    return
                cnt += 1
                print('https://otvet.mail.ru/question/' + str(i['id']))

    def search(self, query):
        res = json.loads(self.opener.open('https://go.mail.ru/answer_json?num=1&q=' + urllib.parse.quote(query)).read().decode())
        try:
            qid = res['results'][0]['id']
        except LookupError:
            return None
        q = self.readQuestion(qid)
        if 'best' in q:
            return q['best']['atext']
        try:
            return q['answers'][0]['atext']
        except LookupError:
            return None

    def enumStarredQuestions(self):
        res = []
        for i in self.apiCall('leadqst')['qst'][::-1]:
            if i['id'] in self.answered_questions:
                continue
            self.answered_questions.add(i['id'])
            res.append(self.readQuestion(i['id']))
        return res

    def answerQuestion(self, qid, answer):
        resp = self.apiCall('addans', {'qid': qid, 'Body': answer, 'source': ''}, 'post')
        if 'errid' in resp:
            if resp['errid'] == 118:  # already answered
                return True
            elif resp['errid'] == 112:  # too long
                print('Too long')
                return True
            elif resp['errid'] == 221:
                print('Limit reached')
                return False
            elif resp['errid'] == 216:
                print('Too many images')
                return True
            elif resp['errid'] == 237:
                print('Captcha needed')
                return False
            elif resp['errid'] == 109:
                print('Spam words')
                return True
            elif resp['errid'] == 161:
                print('Hidden')
                return True
            print(resp)
            return False
        return True
