import base64
import getpass
from random import randint
import os
import socket
import sys
import time
import ssl
import quopri

port = 465


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
    # global login, password, recipient, host
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    else:
        host = sys.argv[1]
    login = input("LOGIN: ")
    password = getpass.getpass('PASS: ')
    recipient = input("RECIPIENT: ")
    return login, password, recipient, host


def gen_mess(login, recipient, all_files):
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
              'Subject: test smtp\r\n'
              'Content-Type: Multipart/mixed; boundary=\"{2}\"\r\n')
    result = result.format(login, recipient, delim)
    result += ('--' + delim + '\r\n'
               'Content-Type: text/plain; charset=utf-8\r\n'
               'Content-transfer-encoding: base64\r\n'
               '\r\n' +
               to_base64('ну позязя')
               + '\r\n'
               )
    for f, content in all_files.items():
        result += ('--{2}\r\n'
                   'Content-Type: application/octet-stream; name=\"{4}\"\r\n'
                   'Content-transfer-encoding: base64\r\n'
                   'Content-Disposition: attachment; filename=\"{4}\"\r\n'
                   '\r\n'
                   '{3}\r\n')
        result = result.format(
            login,
            recipient,
            delim,
            content.decode('utf-8'),
            f
        )
    return result


def gen_dict_of_images():
    all_files = {}
    for f in os.listdir("./"):
        ext = ['.jpg', '.png', '.jpeg']
        is_image = filter(f.lower().endswith, ext)
        if list(is_image):
            with open(f, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                all_files[f] = encoded_string
    return all_files


def send(msg, sock):
    sock.send((msg + '\r\n').encode('utf-8'))
    print(recv_data(sock))


def send_and_print(msg, sock):
    print(msg)
    sock.send((msg + '\r\n').encode('utf-8'))
    print(recv_data(sock))


def to_base64(s):
    encoded_s = base64.b64encode(bytes(s, 'utf-8'))
    return encoded_s.decode('utf-8')


def create_and_send_mess(sock, login, password, recipient, all_files):
    print(recv_data(sock))
    messages = [
        'helo vintik9g',
        'auth login',
        to_base64('{0}'.format(login)),
        to_base64('{0}'.format(password)),
        'mail from: <{0}>'.format(login),
        'rcpt to: <{0}>'.format(recipient),
        'data'
    ]
    for m in messages:
        send_and_print(m, sock)
    send(gen_mess(login, recipient, all_files) + '\r\n.', sock)


def main():
    login, password, recipient, host = get_args()
    print(host + ' ' + repr(port))
    sock = ssl.SSLSocket(socket.socket())
    sock.connect((host, port))

    all_files = gen_dict_of_images()
    print("\nyou have {0} img files\n".format(len(all_files)))

    create_and_send_mess(sock, login, password, recipient, all_files)


if __name__ == "__main__":
    main()
