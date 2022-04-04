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
    print('getting block\n')
    if crypto == 'btc' or crypto == 'bch':
        result = subprocess.run(['bitcoin-cli', 'getblock', '{}'.format(hash), "1"], stdout=subprocess.PIPE)
    elif crypto == 'ltc':
        result = subprocess.run(['litecoin-cli', 'getblock', '{}'.format(hash), "1"], stdout=subprocess.PIPE)
    elif crypto == 'doge':
        result =subprocess.run(['dogecoin-cli', 'getblock', '{}'.format(hash), "true"], stdout=subprocess.PIPE)
    else:
        print('invalid crypto')
        return
    result = result.stdout.decode("utf-8")
    if result and 'error' not in result:
        try:
            result = json.loads(result)
            txs = result['tx']
        except Exception as e:
            logging.exception('failed json manipulation')
            return

        cur2 = conn.cursor()
        try:
            for tx in txs:
                try:
                    cur2.execute("insert into tx_hashes values (?, ?)", (str(tx).strip(), hash.strip()))
                except Exception as e:
                    logging.exception('failed block info insert')
                    continue
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
