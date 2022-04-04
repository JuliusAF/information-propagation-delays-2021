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


def get_block_info(hash, conn, crypto):
    cur = conn.cursor()
    print('getting block\n')
    if crypto == 'btc' or crypto == 'bch':
        result = subprocess.run(['bitcoin-cli', 'getblock', '{}'.format(hash), "1"], stdout=subprocess.PIPE)
        cli = 'bitcoin-cli'
    elif crypto == 'ltc':
        result = subprocess.run(['litecoin-cli', 'getblock', '{}'.format(hash), "1"], stdout=subprocess.PIPE)
        cli = 'litecoin-cli'
    elif crypto == 'doge':
        result =subprocess.run(['dogecoin-cli', 'getblock', '{}'.format(hash), "true"], stdout=subprocess.PIPE)
        cli = 'dogecoin-cli'
    else:
        print('invalid crypto')
        return
    result = result.stdout.decode("utf-8")
    if result and 'error' not in result:
        try:
            result = json.loads(result)
            del result['tx']
            height = result['height']
            getblock = json.dumps(result, indent=4)
        except Exception as e:
            logging.exception('failed json manipulation')
            return
        print('getting block stats\n')
        result = subprocess.run([cli, 'getblockstats', '{}'.format(height)], stdout=subprocess.PIPE)
        result = result.stdout.decode("utf-8")
        if result and 'error' not in result:
            cur2 = conn.cursor()
            try:
                cur2.execute("insert into blocks values (?, ?, ?, ?)", (time.time(), hash, getblock, result))
            except Exception as e:
                logging.exception('failed block info insert')
        else:
            cur2 = conn.cursor()
            try:
                cur2.execute("insert into blocks values (?, ?, ?, ?)", (time.time(), hash, getblock, None))
            except Exception as e:
                logging.exception('failed block info insert')


if __name__ == '__main__':
    db = input("db path\n")
    crypto = input('crypto\n')
    start = int(input('start height\n'))
    end = int(input('end height\n'))
    conn = create_connection(db)
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
        print(result)
        get_block_info(result.strip(), conn, crypto)

    conn.commit()
    conn.close()
