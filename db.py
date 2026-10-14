import sqlite3

DB_PATH = "data/sentinel.db"


def get_connection():
    return sqlite3.connect(DB_PATH)

def get_recent_transactions(account_id: str, limit: int = 20):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT txn_id, ts, amount, channel, ip_country, auth_result,
               merchant_id, device_id
        FROM transactions
        WHERE account_id = ?
        ORDER BY ts DESC
        LIMIT ?
        """,
        (account_id, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_transaction_summary(account_id: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS transaction_count,
            AVG(amount) AS average_amount,
            MIN(amount) AS minimum_amount,
            MAX(amount) AS maximum_amount,
            SUM(CASE WHEN auth_result = 'declined' THEN 1 ELSE 0 END) AS declined_count
        FROM transactions
        WHERE account_id = ?
        """,
        (account_id,),
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row)

def get_historical_transaction_summary(account_id: str, exclude_recent: int = 20):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS transaction_count,
            AVG(amount) AS average_amount,
            MIN(amount) AS minimum_amount,
            MAX(amount) AS maximum_amount,
            SUM(CASE WHEN auth_result = 'declined' THEN 1 ELSE 0 END) AS declined_count
        FROM transactions
        WHERE account_id = ?
          AND txn_id NOT IN (
              SELECT txn_id
              FROM transactions
              WHERE account_id = ?
              ORDER BY ts DESC
              LIMIT ?
          )
        """,
        (account_id, account_id, exclude_recent),
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row)

def get_case_notes(account_id: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            n.note_id,
            n.created_at,
            n.author,
            n.channel,
            n.note
        FROM case_notes n
        JOIN accounts a
            ON a.customer_id = n.customer_id
        WHERE a.account_id = ?
        ORDER BY n.created_at DESC
        """,
        (account_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_disputes(account_id: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            d.dispute_id,
            d.txn_id,
            d.filed_at,
            d.reason_code,
            d.customer_statement,
            d.status
        FROM disputes d
        JOIN transactions t
            ON t.txn_id = d.txn_id
        WHERE t.account_id = ?
        ORDER BY d.filed_at DESC
        """,
        (account_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_prior_cases(account_id: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            p.case_id,
            p.opened_date,
            p.closed_date,
            p.outcome,
            p.summary
        FROM prior_cases p
        JOIN accounts a
            ON a.customer_id = p.customer_id
        WHERE a.account_id = ?
        ORDER BY p.opened_date DESC
        """,
        (account_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_shared_devices(account_id: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.device_id,
            COUNT(DISTINCT t.account_id) AS account_count,
            GROUP_CONCAT(DISTINCT t.account_id) AS accounts
        FROM transactions t
        WHERE t.device_id IN (
            SELECT DISTINCT device_id
            FROM transactions
            WHERE account_id = ?
              AND device_id IS NOT NULL
        )
        GROUP BY t.device_id
        HAVING COUNT(DISTINCT t.account_id) > 1
        ORDER BY account_count DESC
        """,
        (account_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_shared_merchants(account_id: str, limit: int = 10):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            t.merchant_id,
            m.name AS merchant_name,
            m.category,
            m.country,
            m.risk_score,
            COUNT(DISTINCT t.account_id) AS account_count
        FROM transactions t
        JOIN merchants m
            ON m.merchant_id = t.merchant_id
        WHERE t.merchant_id IN (
            SELECT DISTINCT merchant_id
            FROM transactions
            WHERE account_id = ?
              AND merchant_id IS NOT NULL
        )
        GROUP BY
            t.merchant_id,
            m.name,
            m.category,
            m.country,
            m.risk_score
        ORDER BY m.risk_score DESC, account_count DESC
        LIMIT ?
        """,
        (account_id, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_alerted_accounts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT account_id
        FROM alerts
        ORDER BY account_id
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]