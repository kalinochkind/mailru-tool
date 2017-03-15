#!/usr/bin/python3

from parser import MailruParser
import sys
import time

def main():
    try:
        f = open('bot_login.txt')
    except Exception:
        print('Failed to get credentials')
        return
    for line in f:
        if not line.strip() or line.startswith('#'):
            continue
        login, password = line.split()
        mailru = MailruParser(login, password)
        print(login)
        if not mailru.token:
            continue
        last_qid = int(mailru.readPage(0, 'A', 10)[0]['id'])
        time.sleep(5)
        while mailru:
            for i in reversed(mailru.readPage(0, 'A', 10)):
                if int(i['id']) <= last_qid:
                    continue
                last_qid = int(i['id'])
                q = mailru.readQuestion(i['id'])
                if 'qid' not in q:
                    print('Invalid response, skipping')
                    continue
                if q.get('qcomment', '').strip():
                    print(q['qid'], 'has a comment, skipping')
                    continue
                if q.get('polltype') in ('S', 'C'):
                    print(q['qid'], 'is a poll, skipping')
                    continue
                text = q.get('qtext', '')
                result = mailru.search(text)
                time.sleep(2)
                if not result:
                    print(q['qid'], 'no answer found, skipping')
                    continue
                if '<a' in result or '<img' in result:
                    print(q['qid'], 'has links or images, skipping')
                    continue
                if not mailru.answerQuestion(q['qid'], result):
                    mailru = None
                    print('Finished\n')
                    break
                print('\n{}: {}\n\nAnswer: {}\n'.format(q['qid'], text, result))
            time.sleep(5)

if __name__ == '__main__':
    main()
