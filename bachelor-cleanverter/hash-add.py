import time
import sqlite3
import subprocess
import json
import logging


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        logging.exception("couldnt open db connection")

    return conn


if __name__ == '__main__':
    db = input("db path\n")
    crypto = input('crypto\n')
    start = int(input('start height\n'))
    end = int(input('end height\n'))
    conn = create_connection(db)
    cursor = conn.cursor()
    if conn is None:
        logging.debug('couldnt open conn')

    for i in range(start, end):
        print('getting hash\n')
        if crypto == 'btc' or crypto == 'bch':
            result = subprocess.run(['bitcoin-cli', 'getblockhash', '{}'.format(i)], stdout=subprocess.PIPE)
        elif crypto == 'ltc':
            result = subprocess.run(['litecoin-cli', 'getblockhash', '{}'.format(i)], stdout=subprocess.PIPE)
        elif crypto == 'doge':
            result = subprocess.run(['dogecoin-cli', 'getblockhash', '{}'.format(i)], stdout=subprocess.PIPE)
        else:
            print('invalid crypto')
            result = None
        result = result.stdout.decode("utf-8")
        if result:
            cursor.execute("insert into valid_blocks values (?)", (result,))

    conn.commit()
    conn.close()
