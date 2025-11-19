from gemini_bot import GeminiBot
from data_loader import DataLoader
import pandas as pd
import re

class SalesBot:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.gemini = GeminiBot()
        self.conversation_history = []
    
    def start(self):
        print("\n" + "=" * 60)
        print("SALES & ORDERS BOT")
        print("=" * 60)
        print("Ask me anything about sales and orders in natural language")
        print("Type 'menu' to return to main menu")
        print("=" * 60 + "\n")
        
        while True:
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'menu', 'back']:
                print("Returning to main menu...\n")
                self.conversation_history = []
                break
            
            response = self.process_query(query)
            print(f"\nBot: {response}\n")
    
    def extract_numbers(self, query):
        numbers = re.findall(r'\b\d+\b', query)
        return [int(n) for n in numbers]
    
    def extract_time_period(self, query):
        query_lower = query.lower()
        
        if 'today' in query_lower:
            return {'type': 'days', 'value': 1}
        if 'yesterday' in query_lower:
            return {'type': 'days', 'value': 1}
        if 'week' in query_lower:
            numbers = self.extract_numbers(query)
            weeks = numbers[0] if numbers else 1
            return {'type': 'days', 'value': weeks * 7}
        if 'month' in query_lower:
            numbers = self.extract_numbers(query)
            months = numbers[0] if numbers else 1
            return {'type': 'days', 'value': months * 30}
        
        days_match = re.search(r'(\d+)\s*days?', query_lower)
        if days_match:
            return {'type': 'days', 'value': int(days_match.group(1))}
        
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in query_lower:
                return {'type': 'month', 'value': month_num}
        
        return None
    
    def understand_intent_with_ai(self, query):
        context = f"""Analyze this user query about sales/orders and determine the intent. Return ONLY the intent name.

Available intents:
- order_details: User wants details about a specific order number
- recent_orders: User wants to see recent orders
- sales_summary: User wants overall sales summary or report
- top_customers: User wants to see top spending customers
- revenue_info: User wants revenue/income information
- average_order: User wants average order value
- payment_status: User wants to know about paid/unpaid orders
- popular_items: User wants to see top selling items
- payment_methods: User wants to see payment method breakdown
- time_period_sales: User wants sales for a specific time period
- orders_in_queue: User wants to see orders that are pending/in queue
- general_question: General question about sales

User query: "{query}"

Return only one word - the intent name."""
        
        intent = self.gemini.get_response(context, "").strip().lower()
        return intent
    
    def process_query(self, query):
        self.conversation_history.append(query)
        
        intent = self.understand_intent_with_ai(query)
        numbers = self.extract_numbers(query)
        time_period = self.extract_time_period(query)
        
        # Handle "in queue" or pending orders
        if 'queue' in intent or 'queue' in query.lower() or 'pending' in query.lower():
            return self.get_orders_in_queue()
        
        if 'order_details' in intent and numbers:
            return self.get_order_details(numbers[0])
        
        if 'recent' in intent and time_period:
            return self.get_recent_orders_by_days(time_period['value'])
        
        if 'recent' in intent:
            return self.get_recent_orders(10)
        
        if 'top_customers' in intent or 'top_member' in intent:
            limit = numbers[0] if numbers else 10
            return self.get_top_members(limit)
        
        if 'time_period' in intent and time_period:
            if time_period['type'] == 'month':
                return self.get_monthly_sales_report(time_period['value'])
            else:
                return self.get_recent_orders_by_days(time_period['value'])
        
        if 'sales_summary' in intent:
            return self.get_sales_summary()
        
        if 'revenue' in intent:
            return self.get_revenue_summary()
        
        if 'average' in intent:
            return self.get_average_order()
        
        if 'payment_status' in intent:
            if 'unpaid' in query.lower() or 'pending' in query.lower():
                return self.get_unpaid_orders()
            else:
                return self.get_completed_orders()
        
        if 'popular' in intent or 'items' in intent:
            return self.get_top_items()
        
        if 'payment_methods' in intent:
            return self.get_payment_methods()
        
        return self.intelligent_response(query)
    
    def get_orders_in_queue(self):
        """Get orders that are pending payment"""
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to order data right now."
        
        status_col = next((c for c in orders_df.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        
        if status_col is None:
            return "I can't find the payment status column."
        
        # Fixed: Use .copy() to avoid SettingWithCopyWarning
        pending_orders = orders_df[orders_df[status_col].astype(str) != 'Paid'].copy()
        
        if len(pending_orders) == 0:
            return "Great news! There are no orders in queue. All orders have been paid."
        
        amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        if amount_col:
            pending_orders[amount_col] = pd.to_numeric(pending_orders[amount_col], errors='coerce')
            total_pending = pending_orders[amount_col].sum()
        else:
            total_pending = 0
        
        info = f"""
ORDERS IN QUEUE (PENDING PAYMENT):
{'=' * 60}
Total Orders in Queue: {len(pending_orders):,}
Total Pending Amount: CAD ${total_pending:,.2f}
{'=' * 60}

RECENT PENDING ORDERS:
"""
        
        order_num_col = next((c for c in orders_df.columns if 'order' in c.lower() and 'number' in c.lower()), None)
        date_col = next((c for c in orders_df.columns if 'date' in c.lower() and 'created' in c.lower()), None)
        email_col = next((c for c in orders_df.columns if 'email' in c.lower()), None)
        
        for idx, order in pending_orders.head(10).iterrows():
            order_num = str(order.get(order_num_col, 'N/A')) if order_num_col else 'N/A'
            date_val = str(order.get(date_col, 'N/A')) if date_col else 'N/A'
            email = str(order.get(email_col, 'N/A')) if email_col else 'N/A'
            status = str(order.get(status_col, 'N/A')) if status_col else 'N/A'
            amount = order.get(amount_col, 0) if amount_col else 0
            
            info += f"\nOrder #{order_num} - {date_val}"
            info += f"\nCustomer: {email}"
            info += f"\nStatus: {status} | Amount: CAD ${amount:.2f}\n"
        
        if len(pending_orders) > 10:
            info += f"\n... and {len(pending_orders) - 10} more pending orders"
        
        return info
    
    def get_order_details(self, order_num):
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to order data right now."
        
        order_num_col = next((c for c in orders_df.columns if 'order' in c.lower() and 'number' in c.lower()), None)
        
        if order_num_col is None:
            return "I can't find the order number column in the database."
        
        # Fixed: Use proper boolean indexing with conversion to numeric
        orders_df[order_num_col] = pd.to_numeric(orders_df[order_num_col], errors='coerce')
        order = orders_df[orders_df[order_num_col] == order_num]
        
        if len(order) == 0:
            return f"I couldn't find any order with number {order_num}. Would you like to check a different order?"
        
        order = order.iloc[0]
        
        date_col = next((c for c in orders_df.columns if 'date' in c.lower() and 'created' in c.lower()), None)
        email_col = next((c for c in orders_df.columns if 'email' in c.lower()), None)
        status_col = next((c for c in orders_df.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        def safe_get(col, default='N/A'):
            if col is None:
                return default
            val = order.get(col)
            return str(val) if pd.notna(val) else default
        
        info = f"""
ORDER #{order_num} DETAILS:
{'=' * 60}
Date: {safe_get(date_col)}
Customer: {safe_get(email_col)}
Status: {safe_get(status_col)}
Amount: CAD ${order.get(amount_col, 0):.2f if amount_col and pd.notna(order.get(amount_col)) else 0}
{'=' * 60}

ITEMS ORDERED:
"""
        
        items_df = self.data_loader.get_dataframe('items_purchased')
        if items_df is not None:
            item_order_col = next((c for c in items_df.columns if 'order' in c.lower() and 'number' in c.lower()), None)
            
            if item_order_col:
                items_df[item_order_col] = pd.to_numeric(items_df[item_order_col], errors='coerce')
                items = items_df[items_df[item_order_col] == order_num]
                
                if len(items) > 0:
                    item_col = next((c for c in items.columns if 'item' in c.lower() and 'order' not in c.lower()), None)
                    qty_col = next((c for c in items.columns if 'qty' in c.lower() or 'quantity' in c.lower()), None)
                    item_amount_col = next((c for c in items.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
                    
                    for idx, item in items.iterrows():
                        item_name = str(item.get(item_col, 'Unknown Item')) if item_col else 'Unknown Item'
                        qty = item.get(qty_col, 1) if qty_col else 1
                        item_amount = item.get(item_amount_col, 0) if item_amount_col else 0
                        info += f"{item_name} (Qty: {qty}) - CAD ${item_amount:.2f}\n"
                else:
                    info += "No item details available\n"
            else:
                info += "No item details available\n"
        else:
            info += "No item details available\n"
        
        return info
    
    def get_recent_orders(self, limit=10):
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to order data right now."
        
        recent = orders_df.head(limit)
        
        order_num_col = next((c for c in orders_df.columns if 'order' in c.lower() and 'number' in c.lower()), None)
        date_col = next((c for c in orders_df.columns if 'date' in c.lower() and 'created' in c.lower()), None)
        email_col = next((c for c in orders_df.columns if 'email' in c.lower()), None)
        status_col = next((c for c in orders_df.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        def safe_get(row, col, default='N/A'):
            if col is None:
                return default
            val = row.get(col)
            return str(val) if pd.notna(val) else default
        
        info = f"HERE ARE THE {limit} MOST RECENT ORDERS:\n{'=' * 60}\n\n"
        
        for idx, order in recent.iterrows():
            order_num = safe_get(order, order_num_col)
            date_val = safe_get(order, date_col)
            email = safe_get(order, email_col)
            status = safe_get(order, status_col)
            amount = order.get(amount_col, 0) if amount_col and pd.notna(order.get(amount_col)) else 0
            
            info += f"Order #{order_num} - {date_val}\n"
            info += f"Customer: {email}\n"
            info += f"Status: {status} | Amount: CAD ${amount:.2f}\n\n"
        
        return info
    
    def get_recent_orders_by_days(self, days):
        orders = self.data_loader.get_orders_by_date_range(days=days)
        
        if orders is None or len(orders) == 0:
            return f"I couldn't find any orders from the last {days} days."
        
        amount_col = next((c for c in orders.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        status_col = next((c for c in orders.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        
        if amount_col:
            orders[amount_col] = pd.to_numeric(orders[amount_col], errors='coerce')
            total_amount = orders[amount_col].sum()
            avg_amount = total_amount / len(orders) if len(orders) > 0 else 0
        else:
            total_amount = 0
            avg_amount = 0
        
        paid_count = len(orders[orders[status_col] == 'Paid']) if status_col else 0
        
        info = f"""
SALES FROM LAST {days} DAYS:
{'=' * 60}
Total Orders: {len(orders)}
Paid Orders: {paid_count}
Total Revenue: CAD ${total_amount:,.2f}
Average Order: CAD ${avg_amount:.2f}
{'=' * 60}

RECENT ORDERS:
"""
        
        order_num_col = next((c for c in orders.columns if 'order' in c.lower() and 'number' in c.lower()), None)
        date_col = next((c for c in orders.columns if 'date' in c.lower() and 'created' in c.lower()), None)
        email_col = next((c for c in orders.columns if 'email' in c.lower()), None)
        
        def safe_get(row, col, default='N/A'):
            if col is None:
                return default
            val = row.get(col)
            return str(val) if pd.notna(val) else default
        
        for idx, order in orders.head(10).iterrows():
            order_num = safe_get(order, order_num_col)
            date_val = safe_get(order, date_col)
            email = safe_get(order, email_col)
            status = safe_get(order, status_col)
            amount = order.get(amount_col, 0) if amount_col and pd.notna(order.get(amount_col)) else 0
            
            info += f"\nOrder #{order_num} - {date_val}"
            info += f"\nCustomer: {email}"
            info += f"\nStatus: {status} | Amount: CAD ${amount:.2f}\n"
        
        if len(orders) > 10:
            info += f"\n... and {len(orders) - 10} more orders"
        
        return info
    
    def get_monthly_sales_report(self, month):
        orders = self.data_loader.get_orders_by_month(month)
        
        if orders is None or len(orders) == 0:
            month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            return f"I couldn't find any orders for {month_names[month]}."
        
        amount_col = next((c for c in orders.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        status_col = next((c for c in orders.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        
        if amount_col:
            orders[amount_col] = pd.to_numeric(orders[amount_col], errors='coerce')
            total_revenue = orders[amount_col].sum()
            avg_order = total_revenue / len(orders) if len(orders) > 0 else 0
        else:
            total_revenue = 0
            avg_order = 0
        
        total_orders = len(orders)
        paid_orders = len(orders[orders[status_col] == 'Paid']) if status_col else 0
        refunded_orders = len(orders[orders[status_col] == 'Refunded']) if status_col else 0
        
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        info = f"""
{month_names[month].upper()} SALES REPORT:
{'=' * 60}
Total Orders: {total_orders}
Paid Orders: {paid_orders}
Refunded Orders: {refunded_orders}
Total Revenue: CAD ${total_revenue:,.2f}
Average Order: CAD ${avg_order:.2f}
{'=' * 60}
"""
        
        return info
    
    def get_top_members(self, limit=10):
        top_members = self.data_loader.get_top_members_by_spending(limit)
        
        if top_members is None:
            return "I couldn't retrieve the top customers data right now."
        
        info = f"TOP {limit} CUSTOMERS BY SPENDING:\n{'=' * 60}\n\n"
        
        for idx, row in top_members.iterrows():
            info += f"{idx + 1}. {row['email']}\n"
            info += f"   Orders: {int(row['order_count'])} | Total: CAD ${row['total_spent']:,.2f}\n\n"
        
        return info
    
    def get_sales_summary(self):
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to sales data right now."
        
        total_orders = len(orders_df)
        
        status_col = next((c for c in orders_df.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        paid_orders = len(orders_df[orders_df[status_col] == 'Paid']) if status_col else 0
        refunded = len(orders_df[orders_df[status_col] == 'Refunded']) if status_col else 0
        
        if amount_col:
            orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
            total_revenue = orders_df[amount_col].sum()
            avg_order = total_revenue / total_orders if total_orders > 0 else 0
        else:
            total_revenue = 0
            avg_order = 0
        
        info = f"""
OVERALL SALES SUMMARY:
{'=' * 60}
Total Orders: {total_orders:,}
Paid Orders: {paid_orders:,}
Refunded Orders: {refunded:,}
Conversion Rate: {(paid_orders/total_orders*100):.1f}%

Total Revenue: CAD ${total_revenue:,.2f}
Average Order: CAD ${avg_order:.2f}
{'=' * 60}
"""
        
        return info
    
    def get_revenue_summary(self):
        stats = self.data_loader.get_summary_stats()
        orders_df = self.data_loader.get_dataframe('orders')
        
        info = f"""
REVENUE SUMMARY:
{'=' * 60}
Total Revenue: CAD ${stats.get('total_revenue', 0):,.2f}
"""
        
        if orders_df is not None:
            amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
            if amount_col:
                orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
                avg_order = orders_df[amount_col].mean()
                info += f"Average Order Value: CAD ${avg_order:.2f}\n"
        
        info += f"""
Total Orders: {stats.get('total_orders', 0):,}
Paid Orders: {stats.get('paid_orders', 0):,}
{'=' * 60}
"""
        
        return info
    
    def get_average_order(self):
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to order data right now."
        
        amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        if amount_col is None:
            return "I can't find the amount column in the database."
        
        orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
        avg_order = orders_df[amount_col].mean()
        
        return f"The average order value is CAD ${avg_order:.2f}"
    
    def get_completed_orders(self):
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to order data right now."
        
        status_col = next((c for c in orders_df.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        
        if status_col is None:
            return "I can't find the payment status column."
        
        completed = len(orders_df[orders_df[status_col] == 'Paid'])
        total = len(orders_df)
        percentage = (completed / total * 100) if total > 0 else 0
        
        return f"You have {completed:,} completed (paid) orders out of {total:,} total orders ({percentage:.1f}%)"
    
    def get_unpaid_orders(self):
        orders_df = self.data_loader.get_dataframe('orders')
        
        if orders_df is None:
            return "I don't have access to order data right now."
        
        status_col = next((c for c in orders_df.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        
        if status_col is None:
            return "I can't find the payment status column."
        
        total = len(orders_df)
        paid = len(orders_df[orders_df[status_col] == 'Paid'])
        unpaid = total - paid
        percentage = (unpaid / total * 100) if total > 0 else 0
        
        return f"You have {unpaid:,} unpaid orders out of {total:,} total orders ({percentage:.1f}%)"
    
    def get_top_items(self, limit=10):
        items_df = self.data_loader.get_dataframe('items_purchased')
        
        if items_df is None:
            return "I don't have access to items data right now."
        
        item_col = next((c for c in items_df.columns if 'item' in c.lower() and 'order' not in c.lower()), None)
        amount_col = next((c for c in items_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        if item_col is None:
            return "I can't find the item column in the database."
        
        top_items = items_df[item_col].value_counts().head(limit)
        
        info = f"TOP {limit} SELLING ITEMS:\n{'=' * 60}\n\n"
        
        for idx, (item, count) in enumerate(top_items.items(), 1):
            if amount_col:
                items_df[amount_col] = pd.to_numeric(items_df[amount_col], errors='coerce')
                item_sales = items_df[items_df[item_col] == item]
                total_sales = item_sales[amount_col].sum()
                info += f"{idx}. {item}\n"
                info += f"   Sales: {count} | Revenue: CAD ${total_sales:,.2f}\n\n"
            else:
                info += f"{idx}. {item}\n"
                info += f"   Sales: {count}\n\n"
        
        return info
    
    def get_payment_methods(self):
        payments_df = self.data_loader.get_dataframe('payments')
        
        if payments_df is None:
            return "I don't have access to payment data right now."
        
        method_col = next((c for c in payments_df.columns if 'method' in c.lower()), None)
        amount_col = next((c for c in payments_df.columns if 'amount' in c.lower() and 'processing' not in c.lower()), None)
        
        if method_col is None:
            return "I can't find the payment method column."
        
        methods = payments_df[method_col].value_counts()
        
        info = "PAYMENT METHOD BREAKDOWN:\n" + "=" * 60 + "\n\n"
        
        for method, count in methods.items():
            percentage = (count / len(payments_df)) * 100
            if amount_col:
                payments_df[amount_col] = pd.to_numeric(payments_df[amount_col], errors='coerce')
                method_payments = payments_df[payments_df[method_col] == method]
                total_amount = method_payments[amount_col].sum()
                info += f"{method}\n"
                info += f"Transactions: {count} ({percentage:.1f}%)\n"
                info += f"Total: CAD ${total_amount:,.2f}\n\n"
            else:
                info += f"{method}: {count} transactions ({percentage:.1f}%)\n\n"
        
        return info
    
    def intelligent_response(self, query):
        stats = self.data_loader.get_summary_stats()
        orders_df = self.data_loader.get_dataframe('orders')
        
        context_data = f"""Sales & Orders Statistics:
- Total Orders: {stats.get('total_orders', 0):,}
- Paid Orders: {stats.get('paid_orders', 0):,}
- Total Revenue: CAD ${stats.get('total_revenue', 0):,.2f}
"""
        
        if orders_df is not None:
            amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
            if amount_col:
                orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
                avg_order = orders_df[amount_col].mean()
                context_data += f"- Average Order Value: CAD ${avg_order:.2f}\n"
        
        context = f"""You are a helpful sales and orders assistant for a gym. Answer the user's question based on the data provided.

{context_data}

User question: "{query}"

Provide a clear, conversational answer. If you need more specific information to answer better, ask the user politely."""
        
        return self.gemini.get_response(query, context)