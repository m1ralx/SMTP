import base64
import getpass
from random import randint
import socket
import sys
import time
import ssl
import json


def recv_data(sock, timeout=2):
    sock.setblocking(0)
    total_data = []
    begin = time.time()
    while 1:
        if total_data and time.time() - begin > timeout:
            break
        elif time.time() - begin > timeout * 2:
            break
        sock.settimeout(2)
        try:
            data = sock.recv(2 ** 20)
            if data:
                total_data.append(data)
                begin = time.time()
            else:
                time.sleep(0.1)
        except ConnectionAbortedError:
            return -1
        except socket.timeout:
            break
    total_data = b''.join(total_data)
    return total_data.decode()


def print_help():
    path = sys.argv[0].split("/")
    name = path[len(path) - 1]
    print("{0} host".format(name))


def get_args():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    else:
        host = sys.argv[1]
    login = input("LOGIN: ")
    password = getpass.getpass('PASS: ')
    return login, password, host


def gen_mess(login, recipient, all_files, subject, text):
    delim = ''
    symb = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'abcdefghijklmnopqrstuvwxyz'
            '1234567890+-#!^;'
            )
    randN = randint(10, 21)
    for i in range(1, randN):
        randInd = randint(0, 64)
        delim += symb[randInd]
    result = ('FROM: {0} <{0}>\r\n'
              'TO: {1} <{1}>\r\n'
              'Subject: =?UTF-8?B?' + to_base64(subject) + '?=\r\n'
              'Content-Type: Multipart/mixed; boundary=\"{2}\"\r\n')
    result = result.format(login, recipient, delim)
    result += ('--' + delim + '\r\n'
               'Content-Type: text/plain; charset=utf-8\r\n'
               'Content-transfer-encoding: base64\r\n'
               '\r\n' +
               to_base64(text)
               + '\r\n'
               )
    for f, content in all_files.items():
        result += ('--{0}\r\n'
                   'Content-Type: application/octet-stream; name=\"{2}\"\r\n'
                   'Content-transfer-encoding: base64\r\n'
                   'Content-Disposition: attachment; filename=\"{2}\"\r\n'
                   '\r\n'
                   '{1}\r\n')
        result = result.format(
            delim,
            content.decode('utf-8'),
            f
        )
    return result


def gen_dict_of_files(attachments):
    all_files = {}
    for f in attachments:
        with open('./message/' + f, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            all_files[f] = encoded_string
    return all_files


def send(msg, sock):
    sock.send((msg + '\r\n').encode('utf-8'))
    recv_data(sock)


def send_and_print(msg, sock):
    sock.send((msg + '\r\n').encode('utf-8'))
    recv_data(sock)


def to_base64(s):
    encoded_s = base64.b64encode(s.encode('utf-8'))
    return encoded_s.decode('utf-8')


def create_and_send_mess(sock, login, password, recipients,
                         all_files, subject, text):
    for recipient in recipients:
        recv_data(sock)
        messages = [
            'helo pieliedie',
            'auth login',
            to_base64('{0}'.format(login)),
            to_base64('{0}'.format(password)),
            'mail from: <{0}> AUTH={0}'.format(login),
            'rcpt to: <{0}>'.format(recipient),
            'data'
        ]
        for m in messages:
            send_and_print(m, sock)
        send(gen_mess(login, recipient, all_files,
                      subject, text) + '\r\n.', sock)


def main():
    port = 465
    login, password, host = get_args()
    print(host + ' ' + repr(port))
    sock = ssl.SSLSocket(socket.socket())
    sock.connect((host, port))
    with open('./message/config.conf', 'r', encoding='utf-8') as dump_f,\
            open('./message/message.txt', 'r', encoding='utf-8') as msg_f:
        dump = json.load(dump_f)
        recipients = dump['recipients']
        attachments = dump['attachments']
        subject = dump['subject']
        text = ''.join(msg_f.readlines())

    all_files = gen_dict_of_files(attachments)
    print("\nyou have {0} files\n".format(len(all_files)))

    create_and_send_mess(sock, login, password, recipients,
                         all_files, subject, text)


if __name__ == "__main__":
    main()
