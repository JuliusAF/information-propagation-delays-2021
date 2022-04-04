import time
import shutil
import sqlite3
import subprocess
import json
import logging
import threading
import re
import os
import ipinfo

# database
DATABASE = 'bitcoin_cash_database.db'
DATABASE_LOCK = threading.Lock()


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        logging.exception("couldnt open db connection")

    return conn


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        logging.exception("couldnt create table")


def setup_db():
    sql_create_propagation_table = """ CREATE TABLE IF NOT EXISTS propagation (
                                                timestamp integer,
                                                id integer,
                                                ip text,
                                                hash text,
                                                prev_hash text,
                                                block_timestamp integer,
                                                message_type text
                                            ); """

    sql_create_ip_info_table = """ CREATE TABLE IF NOT EXISTS ip_info (
                                                    timestamp integer,
                                                    id integer,
                                                    ip text,
                                                    ip_info text,
                                                    ping_time text
                                                ); """

    sql_create_blocks = """ CREATE TABLE IF NOT EXISTS blocks (
                                                    timestamp integer,
                                                    hash text,
                                                    info text,
                                                    stats text
                                                ); """

    sql_create_tx = """ CREATE TABLE IF NOT EXISTS tx_propagation (
                                                    timestamp integer,
                                                    id integer,
                                                    ip text,
                                                    hash text
                                                ); """

    sql_create_conns = """ CREATE TABLE IF NOT EXISTS connections (
                                                    timestamp integer,
                                                    id integer,
                                                    ip text,
                                                    action text
                                                ); """

    conn = create_connection(DATABASE)

    if conn:
        create_table(conn, sql_create_propagation_table)

        create_table(conn, sql_create_ip_info_table)

        create_table(conn, sql_create_blocks)

        create_table(conn, sql_create_tx)

        create_table(conn, sql_create_conns)
        conn.close()
    else:
        logging.error("couldnt create tables")


# log copying
COPY_INTERVAL = 18000
LOG_PATH = '/home/ubuntu/.bitcoin/debug.log'
COPY_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/'
COPIED_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/debug.log'
SHORTER_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/props.log'
TX_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/txs.log'
CONN_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/conns.log'


def get_timestamp_name():
    timestr = time.strftime("%Y-%m-%d--%H-%M-%S")
    return timestr


# copy bitcoin_cash log and empty file, then parse copied log
def copy_file(src=LOG_PATH, dst=COPY_PATH):
    shutil.copy(src, dst)


def parse_log(path):
    DATABASE_LOCK.acquire()
    conn = create_connection(DATABASE)
    if conn is None:
        logging.debug("couldn't open conn")
        DATABASE_LOCK.release()
        return
    cur = conn.cursor()
    header_match = r'.*micros:(\d*).*peer=(\d*).*ipaddr=([^ ]*).*bhash=([^ ]*).*prevhash=([^ ]*).*timestamp=(\d*).*'
    inv_match = r'.*micros:(\d*).*bhash=block ([^ ]*).*peer=(\d*).*ipaddr=([^ ]*).*'
    inv_match_tx = r'.*micros:(\d*).*bhash=[^ ]* ([^ ]*).*peer=(\d*).*ipaddr=([^ ]*).*'
    conn_match = r'.*micros:(\d*).*ip=([^ ]*).*peer=(\d*).*'
    output = open(SHORTER_PATH, 'a', errors='ignore')
    output_conn = open(CONN_PATH, 'a', errors='ignore')
    with open(path, 'r', errors='ignore') as file:
        for line in file:
            try:
                if "got compact" in line:
                    output.write(line)
                    matches = re.search(header_match, line)
                    cur.execute("insert into propagation values (?, ?, ?, ?, ?, ?, ?)",
                                (matches.group(1), matches.group(2), matches.group(3), matches.group(4),
                                 matches.group(5), matches.group(6), "compactblock"))
                elif "got header" in line:
                    output.write(line)
                    matches = re.search(header_match, line)
                    cur.execute("insert into propagation values (?, ?, ?, ?, ?, ?, ?)",
                                (matches.group(1), matches.group(2), matches.group(3), matches.group(4),
                                 matches.group(5), matches.group(6), "headers"))
                elif "got inventory" in line:
                    output.write(line)
                    matches = re.search(inv_match, line)
                    cur.execute("insert into propagation values (?, ?, ?, ?, ?, ?, ?)",
                                (matches.group(1), matches.group(3), matches.group(4), matches.group(2),
                                 None, None, "inventory"))
                elif "got transaction" in line:
                    matches = re.search(inv_match_tx, line)
                    cur.execute("insert into tx_propagation values (?, ?, ?, ?)", (matches.group(1), matches.group(3),
                                                                                   matches.group(4), matches.group(2)))
                elif "ded connection" in line:
                    output_conn.write(line)
                    matches = re.search(conn_match, line)
                    cur.execute('insert into connections values (?, ?, ?, ?)', (matches.group(1), matches.group(3),
                                                                                matches.group(2), 'connect'))
                elif "disconnecting" in line:
                    output_conn.write(line)
                    matches = re.search(conn_match, line)
                    cur.execute('insert into connections values (?, ?, ?, ?)', (matches.group(1), matches.group(3),
                                                                                matches.group(2), 'disconnect'))
            except Exception as e:
                logging.exception("log parse sqlite error")
                print(line)

    output.close()
    output_conn.close()
    conn.commit()
    conn.close()
    DATABASE_LOCK.release()


def clean_log(src=LOG_PATH, dst=COPY_PATH):
    while True:
        time.sleep(COPY_INTERVAL)
        os.system('bitcoin-cli logging "[]" "[\\"net\\"]"')
        time.sleep(.1)
        logging.info("copying and cleaning log")
        copy_file(src, dst)
        open(src, 'w').close()
        os.system('bitcoin-cli logging "[\\"net\\"]"')
        parse_log(COPIED_PATH)


# get current client info to save and parse
PEERS_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/peers/'
PEERS_INTERVAL = 7200
# token for ipinfo.io
TOKEN = 'XXX'


def parse_peer_info(peers):
    DATABASE_LOCK.acquire()
    conn = create_connection(DATABASE)
    if conn is None:
        logging.debug("failed to open conn")
        DATABASE_LOCK.release()
        return
    cur = conn.cursor()
    handler = ipinfo.getHandler(TOKEN)
    for peer in peers:
        ip = peer['addr'][:-5 or None]
        port = peer['addr'][-4 or None:]
        cur.execute("select * from ip_info where ip=?", (ip,))
        ans = cur.fetchall()
        if len(ans) == 0:
            try:
                response = handler.getDetails(ip)
            # store no record into db
            except Exception as e:
                try:
                    cur.execute("insert into ip_info values (?, ?, ?, ?, ?)",
                                (time.time(), peer['id'], ip, "no record", peer['pingtime']))
                except Exception as e:
                    logging.exception("insert peer error")
                    continue
                logging.exception("ip info exception")
                continue

            response = json.dumps(response.all, indent=4)
            try:
                cur.execute("insert into ip_info values (?, ?, ?, ?, ?)",
                            (time.time(), peer['id'], ip, response, peer['pingtime']))
            except Exception as e:
                logging.exception("insert peer error")
                continue

    conn.commit()
    conn.close()
    DATABASE_LOCK.release()


def get_peer_info():
    result = subprocess.run(['bitcoin-cli', 'getpeerinfo'], stdout=subprocess.PIPE)
    result = result.stdout
    # save json in file
    outname = PEERS_PATH + get_timestamp_name() + '.txt'
    out = open(outname, 'w')
    out.write(result.decode("utf-8"))
    out.close()
    peers = json.loads(result)
    parse_peer_info(peers)


def peer_info():
    while True:
        time.sleep(PEERS_INTERVAL)
        logging.info("getting peer info")
        get_peer_info()


# get current chain tips
CHAINTIP_PATH = '/home/ubuntu/documents/logs/bitcoin_cash/chains/'
CHAINTIP_INTERVAL = 14400


def save_chain_tips():
    result = subprocess.run(['bitcoin_cash-cli', 'getchaintips'], stdout=subprocess.PIPE)
    outname = CHAINTIP_PATH + get_timestamp_name() + '.txt'
    out = open(outname, 'w')
    out.write(result.stdout.decode("utf-8"))
    out.close()


def chain_tips():
    while True:
        time.sleep(CHAINTIP_INTERVAL)
        logging.info('getting chain tips')
        save_chain_tips()


# save block info
BLOCK_INTERVAL = 86400


def get_block_info():
    DATABASE_LOCK.acquire()
    conn = create_connection(DATABASE)
    if conn is None:
        logging.debug('couldnt open conn')
        return
    cur = conn.cursor()
    try:
        cur.execute("select timestamp from blocks order by timestamp desc")
    except Exception as e:
        logging.exception('couldnt get timestamp')
        return
    latest = cur.fetchone()
    latest = latest[0] * 1000000 if latest else 0
    try:
        for row in cur.execute("select hash from propagation where timestamp>? group by hash", (latest,)):
            result = subprocess.run(['bitcoin-cli', 'getblock', '{}'.format(row[0]), "1"], stdout=subprocess.PIPE)
            result = result.stdout.decode("utf-8")
            if result and 'error' not in result:
                try:
                    result = json.loads(result)
                    del result['tx']
                    height = result['height']
                    getblock = json.dumps(result, indent=4)
                except Exception as e:
                    logging.exception('failed json manipulation')
                    continue
                result = subprocess.run(['bitcoin_cash-cli', 'getblockstats', '{}'.format(height)], stdout=subprocess.PIPE)
                result = result.stdout.decode("utf-8")
                try:
                    if result and 'error' not in result:
                        cur2 = conn.cursor()
                        cur2.execute("insert into blocks values (?, ?, ?, ?)", (time.time(), row[0], getblock, result))
                        conn.commit()
                    else:
                        cur2 = conn.cursor()=
                        cur2.execute("insert into blocks values (?, ?, ?, ?)", (time.time(), row[0], getblock, None))
                        conn.commit()
                except Exception as e:
                    logging.exception('failed block info insert')
            else:
                print('error: ' + result)
    except Exception as e:
        logging.exception('failed total block info')
    conn.commit()
    conn.close()
    DATABASE_LOCK.release()


def save_block_info():
    while True:
        time.sleep(BLOCK_INTERVAL)
        logging.info('saving block info')
        get_block_info()


if __name__ == '__main__':
    logging.basicConfig(filename="converter-debug.log", level=10)
    logging.info("starting program")
    setup_db()
    peer_info_thread = threading.Thread(target=peer_info)
    chain_tips_thread = threading.Thread(target=chain_tips)
    # block_info_thread = threading.Thread(target=save_block_info)

    peer_info_thread.start()
    chain_tips_thread.start()
    # block_info_thread.start()
    clean_log()
    peer_info_thread.join()
    chain_tips_thread.join()
    # block_info_thread.join()
