#!/usr/bin/python3

from parser import MailruParser


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
