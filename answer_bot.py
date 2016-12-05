#!/usr/bin/python3

from parser import MailruParser
import sys
import time

def main():
    try:
        login, password = open('bot_login.txt').read().split()
    except Exception:
        print('Failed to read credentials')
        return
    mailru = MailruParser(login, password)
    if not mailru.token:
        return
    last_qid = int(mailru.readPage(0, 'A', 10)[0]['id'])
    time.sleep(5)
    while True:
        for i in reversed(mailru.readPage(0, 'A', 10)):
            if int(i['id']) <= last_qid:
                continue
            last_qid = int(i['id'])
            q = mailru.readQuestion(i['id'])
            if q.get('qcomment', '').strip():
                print(q['qid'], 'has a comment, skipping')
                continue
            text = q.get('qtext', '')
            result = mailru.search(text)
            time.sleep(2)
            if not result:
                print(q['qid'], 'no answer found, skipping')
                continue
            print(q['qid'], text, '\n-> ', result)
            if not mailru.answerQuestion(q['qid'], result):
                return
        time.sleep(5)


if __name__ == '__main__':
    main()
