import sqlite3
from src.utils.constants import DB_PATH, SAMPLE_FUND

# 修改数据库初始化函数，增加基金表
def init_database():
    conn = None
    try:
        conn = sqlite3.connect('fund.db')
        c = conn.cursor()
        
        # Check if is_deleted column exists
        c.execute("PRAGMA table_info(fund_transactions)")
        columns = [column[1] for column in c.fetchall()]
        
        # Add is_deleted column if it doesn't exist
        if 'is_deleted' not in columns:
            c.execute('''ALTER TABLE fund_transactions 
                        ADD COLUMN is_deleted INTEGER DEFAULT 0''')
            conn.commit()
            
        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS funds
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    code TEXT UNIQUE)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS fund_transactions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_id INTEGER,
                    time TEXT,
                    buy_price REAL,
                    buy_quantity INTEGER,
                    total_buy REAL,
                    sell_price REAL,
                    sell_quantity INTEGER,
                    total_sell REAL,
                    high REAL,
                    low REAL,
                    open REAL,
                    close REAL,
                    change_percent TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (fund_id) REFERENCES funds (id))''')
        
        # Insert sample data if no data exists
        c.execute("SELECT COUNT(*) FROM funds")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO funds (name, code) VALUES (?, ?)", 
                     ("示例基金", "000001"))
            fund_id = c.lastrowid
            
            sample_data = (fund_id, '2025-04-07', 1.307, 2000, 9159, 0, 0, 0, 
                          1.35, 1.27, 1.35, 1.3053, '-4.62%', 0)
            c.execute('''INSERT INTO fund_transactions 
                        (fund_id, time, buy_price, buy_quantity, total_buy,
                        sell_price, sell_quantity, total_sell,
                        high, low, open, close, change_percent, is_deleted)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_data)
        
        conn.commit()
        
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if is_deleted column exists
        c.execute("PRAGMA table_info(fund_transactions)")
        columns = [column[1] for column in c.fetchall()]
        
        # Add is_deleted column if it doesn't exist
        if 'is_deleted' not in columns:
            c.execute('''ALTER TABLE fund_transactions 
                        ADD COLUMN is_deleted INTEGER DEFAULT 0''')
            conn.commit()
            
        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS funds
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    code TEXT UNIQUE)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS fund_transactions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_id INTEGER,
                    time TEXT,
                    buy_price REAL,
                    buy_quantity INTEGER,
                    total_buy REAL,
                    sell_price REAL,
                    sell_quantity INTEGER,
                    total_sell REAL,
                    high REAL,
                    low REAL,
                    open REAL,
                    close REAL,
                    change_percent TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (fund_id) REFERENCES funds (id))''')
        
        # Insert sample data if no data exists
        c.execute("SELECT COUNT(*) FROM funds")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO funds (name, code) VALUES (?, ?)", 
                     (SAMPLE_FUND['name'], SAMPLE_FUND['code']))
            fund_id = c.lastrowid
            c.execute('''INSERT INTO fund_transactions 
                        (fund_id, time, buy_price, buy_quantity, total_buy,
                        sell_price, sell_quantity, total_sell,
                        high, low, open, close, change_percent, is_deleted)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (fund_id, *SAMPLE_FUND['sample_data']))
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()