from fastmcp import FastMCP
import os
import sqlite3

# Expense database location jahan Claude ke expense records store honge
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

# Categories resource file jise Claude read karke available categories jaan sakta hai
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# Expense tracking MCP server create karta hai
mcp = FastMCP("ExpenseTracker")


def init_db():
    # Expense data store karne ke liye SQLite table create karta hai
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

# Server start hone par database ready karta hai
init_db()


@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    """
    Claude is tool ko use karke naya expense database me add kar sakta hai.

    Example:
    'Today I spent ₹200 on food'
    -> Claude add_expense call karega.
    """

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )

        # Claude ko success status aur expense ID return karta hai
        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool()
def list_expenses(start_date, end_date):
    """
    Claude is tool se given date range ke expenses dekh sakta hai.

    Example:
    'Show my expenses for June 2026'
    -> Claude list_expenses call karega.
    """

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )

        cols = [d[0] for d in cur.description]

        # Claude ko structured expense list return karta hai
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@mcp.tool()
def summarize(start_date, end_date, category=None):
    """
    Claude is tool se expense summary generate kar sakta hai.

    Example:
    'How much did I spend on Food this month?'
    -> Claude summarize call karega.
    """

    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """

        params = [start_date, end_date]

        # Agar Claude specific category puche to filter lagata hai
        if category:
            query += " AND category = ?"
            params.append(category)

        # Category-wise aggregation karta hai
        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)

        cols = [d[0] for d in cur.description]

        # Claude ko summarized spending data return karta hai
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """
    Claude is resource ko read karke valid categories aur
    subcategories samajh sakta hai.
    """

    # Latest categories file read karke Claude ko return karta hai
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    # MCP server start karta hai taaki Claude tools aur resources access kar sake
    mcp.run()