import sqlite3
from datetime import datetime
#import sys
from typing import List, Dict

# ============================================
# Database Initialization
# ============================================
class DatabaseInitializer:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.create_tables()
        self.insert_sample_data()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Products Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                category TEXT NOT NULL
            )''')
        
        # Transactions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                total_amount REAL NOT NULL,
                discount REAL DEFAULT 0,
                transaction_date TEXT NOT NULL
            )''')
        
        # Transaction Items Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY(transaction_id) REFERENCES transactions(transaction_id)
            )''')
        self.conn.commit()

    def insert_sample_data(self):
        products = [
            (1, 'Apple', 0.99, 100, 'Fruits'),
            (2, 'Milk', 2.49, 50, 'Dairy'),
            (3, 'Bread', 1.99, 75, 'Bakery'),
            (4, 'Eggs', 3.49, 60, 'Dairy'),
            (5, 'Chicken', 5.99, 40, 'Meat')
        ]
        cursor = self.conn.cursor()
        cursor.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)
        self.conn.commit()

# ============================================
# Product Management
# ============================================
class ProductManager:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def view_products(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        
        print("\n{:<10} {:<20} {:<10} {:<10} {:<15}".format(
            "ID", "Name", "Price", "Stock", "Category"))
        print("-" * 65)
        for p in products:
            print("{:<10} {:<20} ${:<9.2f} {:<10} {:<15}".format(
                p[0], p[1], p[2], p[3], p[4]))

# ============================================
# Transaction Processing
# ============================================
class TransactionHandler:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.current_cart: List[Dict] = []
        self.discount = 0.0

    def add_to_cart(self):
        try:
            product_id = int(input("Product ID: "))
            quantity = int(input("Quantity: "))

            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
            product = cursor.fetchone()

            if not product:
                print("❌ Product not found!")
                return

            _, name, price, stock, _ = product

            if stock < quantity:
                print(f"❌ Only {stock} available!")
                return

            self.current_cart.append({
                'product_id': product_id,
                'name': name,
                'price': price,
                'quantity': quantity
            })

            with self.conn:
                cursor.execute(
                    "UPDATE products SET quantity = quantity - ? WHERE product_id=?",
                    (quantity, product_id)
                )
            print(f"✅ Added {quantity}x {name}")

        except ValueError:
            print("❌ Invalid input!")

    def apply_discount(self):
        try:
            self.discount = float(input("Enter discount percentage (0-100): "))
            if not 0 <= self.discount <= 100:
                raise ValueError
            print(f"✅ Applied {self.discount}% discount")
        except ValueError:
            print("❌ Invalid discount value!")
            self.discount = 0.0

    def finalize_transaction(self, customer_name: str):
        if not self.current_cart:
            print("❌ Cart is empty!")
            return False

        subtotal = sum(item['price'] * item['quantity'] for item in self.current_cart)
        discount_amount = (subtotal * self.discount) / 100
        total = subtotal - discount_amount
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO transactions (customer_name, total_amount, discount, transaction_date) VALUES (?,?,?,?)",
                    (customer_name, total, self.discount, transaction_date)
                )
                transaction_id = cursor.lastrowid

                for item in self.current_cart:
                    cursor.execute(
                        "INSERT INTO transaction_items (transaction_id, product_id, quantity, price) VALUES (?,?,?,?)",
                        (transaction_id, item['product_id'], item['quantity'], item['price'])
                    )

            self.print_bill(customer_name, transaction_id, subtotal, discount_amount, total)
            self.current_cart = []
            self.discount = 0.0
            return True

        except sqlite3.Error as e:
            print(f"❌ Transaction failed: {e}")
            return False

    def print_bill(self, customer_name: str, trans_id: int, subtotal: float, discount: float, total: float):
        print("\n" + "=" * 50)
        print("{:^50}".format("SUPERMART GROCERY"))
        print("{:^50}".format("123 Main Street, City"))
        print("{:^50}".format("Tel: (555) 123-4567"))
        print("=" * 50)
        print(f"{'Bill No:':<15}{trans_id:>35}")
        print(f"{'Date:':<15}{datetime.now().strftime('%d-%b-%Y %H:%M'):>35}")
        print(f"{'Customer:':<15}{customer_name:>35}")
        print("-" * 50)
        print("{:<25} {:<10} {:<10} {:<10}".format("ITEM", "PRICE", "QTY", "TOTAL"))
        print("-" * 50)
        
        for item in self.current_cart:
            item_total = item['price'] * item['quantity']
            print("{:<25} ${:<9.2f} {:<10} ${:<9.2f}".format(
                item['name'], item['price'], item['quantity'], item_total))
        
        print("-" * 50)
        print("{:<40} ${:<9.2f}".format("SUBTOTAL:", subtotal))
        print("{:<40} {:<9.1f}%".format("DISCOUNT:", self.discount))
        print("{:<40} ${:<9.2f}".format("DISCOUNT AMOUNT:", discount))
        print("=" * 50)
        print("{:<40} ${:<9.2f}".format("GRAND TOTAL:", total))
        print("=" * 50)
        print("{:^50}".format("Thank you for shopping with us!"))
        print("{:^50}".format("Visit again soon!"))
        print("=" * 50 + "\n")

# ============================================
# Main System
# ============================================
class GroceryStoreSystem:
    def __init__(self):
        self.db = DatabaseInitializer()
        self.product_manager = ProductManager(self.db.conn)
        self.transaction_handler = TransactionHandler(self.db.conn)

    def main_menu(self):
        while True:
            print("\n=== GROCERY STORE SYSTEM ===")
            print("1. View Products")
            print("2. New Transaction")
            print("3. Exit")
            
            try:
                choice = input("Enter choice (1-3): ")

                if choice == '1':
                    self.product_manager.view_products()
                elif choice == '2':
                    self.process_transaction()
                elif choice == '3':
                    print("Exiting system...")
                    self.db.conn.close()
                    sys.exit(0)
                else:
                    print("❌ Invalid choice!")

            except KeyboardInterrupt:
                print("\n🛑 Operation cancelled")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    def process_transaction(self):
        self.transaction_handler.current_cart = []
        self.transaction_handler.discount = 0.0
        
        while True:
            print("\n🛒 Transaction Processing")
            print("1. Add Item")
            print("2. Apply Discount")
            print("3. View Cart")
            print("4. Complete Transaction")
            print("5. Cancel Transaction")

            choice = input("Enter choice (1-5): ")

            if choice == '1':
                self.transaction_handler.add_to_cart()
            elif choice == '2':
                self.transaction_handler.apply_discount()
            elif choice == '3':
                self._view_cart()
            elif choice == '4':
                customer_name = input("Enter customer name: ").strip()
                if customer_name:
                    if self.transaction_handler.finalize_transaction(customer_name):
                        return
                else:
                    print("❌ Customer name required!")
            elif choice == '5':
                print("Transaction cancelled!")
                self.transaction_handler.current_cart = []
                return
            else:
                print("❌ Invalid choice!")

    def _view_cart(self):
        if not self.transaction_handler.current_cart:
            print("🛒 Cart is empty!")
            return

        print("\nCurrent Cart:")
        print("{:<25} {:<10} {:<10}".format("Product", "Price", "Qty"))
        print("-" * 45)
        for item in self.transaction_handler.current_cart:
            print("{:<25} ${:<9.2f} {:<10}".format(
                item['name'], item['price'], item['quantity']))
        print(f"\nCurrent Discount: {self.transaction_handler.discount}%")

# ============================================
# Program Entry
# ============================================
if __name__ == "__main__":
    try:
        system = GroceryStoreSystem()
        system.main_menu()
    except KeyboardInterrupt:
        print("\n🛑 System shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        sys.exit(1)
