from gemini_bot import GeminiBot
from data_loader import DataLoader
import pandas as pd
import re

class MemberBot:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.gemini = GeminiBot()
        self.current_member = None
        self.conversation_history = []
    
    def start(self):
        print("\n" + "=" * 60)
        print("MEMBER SUPPORT BOT")
        print("=" * 60)
        print("Ask me anything about members in natural language")
        print("Type 'menu' to return to main menu")
        print("=" * 60 + "\n")
        
        while True:
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'menu', 'back']:
                print("Returning to main menu...\n")
                self.current_member = None
                self.conversation_history = []
                break
            
            response = self.process_query(query)
            print(f"\nBot: {response}\n")
    
    def extract_member_identifier(self, query):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        if emails:
            return emails[0]
        
        member_id_pattern = r'\bM-\d+\b'
        member_ids = re.findall(member_id_pattern, query, re.IGNORECASE)
        if member_ids:
            return member_ids[0]
        
        words = query.split()
        stopwords = ['find', 'search', 'for', 'about', 'member', 'named', 'called', 'is', 'the', 'a', 'an', 'information', 'info', 'details', 'of', 'on']
        potential_names = [w for w in words if w.lower() not in stopwords and len(w) > 2]
        
        if potential_names:
            return ' '.join(potential_names[:2])
        
        return None
    
    def understand_intent_with_ai(self, query):
        context = f"""Analyze this user query and determine the intent. Return ONLY the intent name.

Current member selected: {"Yes - " + str(self.current_member.get('Name', 'Unknown')) if self.current_member is not None else "No"}

Available intents:
- search_member: User wants to find/search for a member
- contact_info: User wants contact details (email, phone)
- activity_info: User wants to know about member activity or last login
- payment_info: User wants payment/spending information
- order_info: User wants order/purchase information
- general_question: General question about current member

User query: "{query}"

Return only one word - the intent name."""
        
        intent = self.gemini.get_response(context, "").strip().lower()
        return intent
    
    def process_query(self, query):
        try:
            self.conversation_history.append(query)
            
            identifier = self.extract_member_identifier(query)
            intent = self.understand_intent_with_ai(query)
            
            if 'search' in intent and identifier:
                if identifier.upper().startswith('M-'):
                    return self.handle_member_id_search(identifier)
                else:
                    return self.handle_member_search(identifier)
            
            # Fixed: Check if current_member is None properly
            if identifier and self.current_member is None:
                return self.handle_member_search(identifier)
            
            # Fixed: Check if current_member exists properly
            if self.current_member is not None:
                if 'contact' in intent:
                    return self.get_contact_info()
                
                if 'activity' in intent:
                    return self.get_member_activity()
                
                if 'payment' in intent:
                    return self.get_member_payments()
                
                if 'order' in intent or 'purchase' in intent:
                    return self.get_member_orders()
                
                if 'general' in intent:
                    return self.answer_with_context(query)
            
            return self.intelligent_response(query)
        except Exception as e:
            import traceback
            print(f"\nError in process_query: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def handle_member_id_search(self, member_id):
        data_df = self.data_loader.get_dataframe('data')
        if data_df is None:
            return "Member data not available."
        
        id_col = next((c for c in data_df.columns if 'member' in c.lower() and 'id' in c.lower()), None)
        if not id_col:
            return "Cannot search by member ID."
        
        # Fixed: Use proper boolean indexing
        member = data_df[data_df[id_col].astype(str).str.upper() == member_id.upper()]
        
        if len(member) == 0:
            return f"No member found with ID {member_id}"
        
        self.current_member = member.iloc[0]
        return self.display_member_info(self.current_member)
    
    def handle_member_search(self, identifier):
        results = self.data_loader.search_member(identifier)
        
        if results is None or len(results) == 0:
            return f"I couldn't find any member matching '{identifier}'. Could you provide more details?"
        
        if len(results) == 1:
            self.current_member = results.iloc[0]
            return self.display_member_info(self.current_member)
        
        return self.format_multiple_results(results, identifier)
    
    def format_multiple_results(self, results, query):
        response = f"I found {len(results)} members matching '{query}':\n\n"
        
        name_col = next((c for c in results.columns if 'name' in c.lower()), None)
        email_col = next((c for c in results.columns if 'email' in c.lower()), None)
        id_col = next((c for c in results.columns if 'member' in c.lower() and 'id' in c.lower()), None)
        
        for idx, row in results.head(5).iterrows():
            name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else 'Unknown'
            email = str(row[email_col]) if email_col and pd.notna(row[email_col]) else 'No email'
            member_id = str(row[id_col]) if id_col and pd.notna(row[id_col]) else 'N/A'
            response += f"{name} ({email}) - ID: {member_id}\n"
        
        if len(results) > 5:
            response += f"\n... and {len(results) - 5} more\n"
        
        response += "\nWhich one would you like to know about?"
        return response
    
    def display_member_info(self, member):
        data_df = self.data_loader.get_dataframe('data')
        cols = data_df.columns.tolist()
        
        def safe_get(key, default='N/A'):
            val = member.get(key)
            return str(val) if pd.notna(val) and val else default
        
        member_id = safe_get('Member_ID', safe_get('Member ID', 'N/A'))
        name = safe_get('Name', 'N/A')
        email = safe_get('Email_Clean', safe_get('Email', 'N/A'))
        phone = safe_get('Phone_Clean', safe_get('Phone', ''))
        
        created_col = next((c for c in cols if 'created' in c.lower()), None)
        activity_col = next((c for c in cols if 'activity' in c.lower()), None)
        source_col = next((c for c in cols if 'source' in c.lower()), None)
        
        created = safe_get(created_col) if created_col else 'N/A'
        last_activity = safe_get(activity_col) if activity_col else 'N/A'
        source = safe_get(source_col) if source_col else 'N/A'
        
        phone_display = phone if phone and phone != '' else 'Not available'
        
        info = f"""
MEMBER INFORMATION:
{'=' * 60}
Member ID: {member_id}
Name: {name}
Email: {email}
Phone: {phone_display}
Joined: {created}
Last Activity: {last_activity}
Source: {source}
{'=' * 60}

What would you like to know about {name}?
"""
        return info
    
    def get_member_activity(self):
        if self.current_member is None:
            return "Please tell me which member you'd like to know about first."
        
        data_df = self.data_loader.get_dataframe('data')
        cols = data_df.columns.tolist()
        
        def safe_get(key, default='Unknown'):
            val = self.current_member.get(key)
            return str(val) if pd.notna(val) and val else default
        
        created_col = next((c for c in cols if 'created' in c.lower()), None)
        activity_col = next((c for c in cols if 'activity' in c.lower()), None)
        source_col = next((c for c in cols if 'source' in c.lower()), None)
        name_col = next((c for c in cols if 'name' in c.lower()), None)
        
        name = safe_get(name_col, 'This member')
        created = safe_get(created_col) if created_col else 'Unknown'
        last_activity = safe_get(activity_col) if activity_col else 'Unknown'
        source = safe_get(source_col) if source_col else 'Unknown'
        
        return f"""
ACTIVITY INFORMATION FOR {name.upper()}:
{'=' * 60}
Joined: {created}
Last Activity: {last_activity}
Acquisition Source: {source}
{'=' * 60}
"""
    
    def get_member_payments(self):
        if self.current_member is None:
            return "Please tell me which member you'd like to know about first."
        
        data_df = self.data_loader.get_dataframe('data')
        email_col = next((c for c in data_df.columns if 'email' in c.lower()), None)
        
        if email_col is None:
            return "I can't determine the member's email to check payments."
        
        email = self.current_member.get(email_col)
        if pd.isna(email) or not email:
            return "This member doesn't have a valid email address."
        
        name_col = next((c for c in data_df.columns if 'name' in c.lower()), None)
        name = str(self.current_member.get(name_col, email)) if name_col else str(email)
        
        payments = self.data_loader.get_member_payments(str(email))
        
        if payments is None or len(payments) == 0:
            return f"{name} hasn't made any payments yet."
        
        # Create a copy to avoid warnings
        payments_copy = payments.copy()
        
        amount_col = next((c for c in payments_copy.columns if 'amount' in c.lower() and 'processing' not in c.lower()), None)
        
        if amount_col:
            payments_copy[amount_col] = pd.to_numeric(payments_copy[amount_col], errors='coerce')
            total_paid = payments_copy[amount_col].sum()
        else:
            total_paid = 0
        
        payment_count = len(payments_copy)
        
        info = f"""
PAYMENT SUMMARY FOR {name.upper()}:
{'=' * 60}
Total Payments: {payment_count}
Total Amount: CAD ${total_paid:,.2f}
{'=' * 60}

RECENT PAYMENTS:
"""
        
        date_col = next((c for c in payments_copy.columns if 'date' in c.lower()), None)
        status_col = next((c for c in payments_copy.columns if 'status' in c.lower()), None)
        method_col = next((c for c in payments_copy.columns if 'method' in c.lower()), None)
        
        for idx, payment in payments_copy.head(5).iterrows():
            date_val = str(payment.get(date_col, 'N/A')) if date_col and pd.notna(payment.get(date_col)) else 'N/A'
            status_val = str(payment.get(status_col, 'N/A')) if status_col and pd.notna(payment.get(status_col)) else 'N/A'
            method_val = str(payment.get(method_col, 'N/A')) if method_col and pd.notna(payment.get(method_col)) else 'N/A'
            
            # Safe amount retrieval
            if amount_col:
                try:
                    amount_val = pd.to_numeric(payment.get(amount_col, 0), errors='coerce')
                    if pd.isna(amount_val):
                        amount_val = 0
                except:
                    amount_val = 0
            else:
                amount_val = 0
            
            info += f"\n{date_val} - CAD ${amount_val:.2f}"
            info += f"\nStatus: {status_val}, Method: {method_val}\n"
        
        if len(payments_copy) > 5:
            info += f"\n... and {len(payments_copy) - 5} more payments"
        
        return info
    
    def get_member_orders(self):
        if self.current_member is None:
            return "Please tell me which member you'd like to know about first."
        
        data_df = self.data_loader.get_dataframe('data')
        email_col = next((c for c in data_df.columns if 'email' in c.lower()), None)
        
        if email_col is None:
            return "I can't determine the member's email to check orders."
        
        email = self.current_member.get(email_col)
        if pd.isna(email) or not email:
            return "This member doesn't have a valid email address."
        
        name_col = next((c for c in data_df.columns if 'name' in c.lower()), None)
        name = str(self.current_member.get(name_col, email)) if name_col else str(email)
        
        orders = self.data_loader.get_member_orders(str(email))
        
        if orders is None or len(orders) == 0:
            return f"{name} hasn't placed any orders yet."
        
        total_orders = len(orders)
        
        status_col = next((c for c in orders.columns if 'status' in c.lower() and 'payment' in c.lower()), None)
        # Fixed: Safe boolean comparison
        if status_col:
            paid_orders = (orders[status_col].astype(str) == 'Paid').sum()
        else:
            paid_orders = 0
        
        amount_col = next((c for c in orders.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
        
        if amount_col:
            orders_copy = orders.copy()
            orders_copy[amount_col] = pd.to_numeric(orders_copy[amount_col], errors='coerce')
            total_spent = orders_copy[amount_col].sum()
        else:
            total_spent = 0
        
        info = f"""
ORDER SUMMARY FOR {name.upper()}:
{'=' * 60}
Total Orders: {total_orders}
Paid Orders: {paid_orders}
Total Spent: CAD ${total_spent:,.2f}
{'=' * 60}

RECENT ORDERS:
"""
        
        order_num_col = next((c for c in orders.columns if 'order' in c.lower() and 'number' in c.lower()), None)
        date_col = next((c for c in orders.columns if 'date' in c.lower() and 'created' in c.lower()), None)
        
        for idx, order in orders.head(5).iterrows():
            order_num = str(order.get(order_num_col, 'N/A')) if order_num_col else 'N/A'
            date_val = str(order.get(date_col, 'N/A')) if date_col else 'N/A'
            status_val = str(order.get(status_col, 'N/A')) if status_col else 'N/A'
            
            # Safe amount retrieval
            if amount_col:
                try:
                    amount_val = pd.to_numeric(order.get(amount_col, 0), errors='coerce')
                    if pd.isna(amount_val):
                        amount_val = 0
                except:
                    amount_val = 0
            else:
                amount_val = 0
            
            info += f"\nOrder #{order_num} - {date_val}"
            info += f"\nStatus: {status_val}, Amount: CAD ${amount_val:.2f}\n"
        
        if len(orders) > 5:
            info += f"\n... and {len(orders) - 5} more orders"
        
        return info
    
    def get_contact_info(self):
        if self.current_member is None:
            return "Please tell me which member you'd like to know about first."
        
        data_df = self.data_loader.get_dataframe('data')
        
        def safe_get(key, default='N/A'):
            val = self.current_member.get(key)
            return str(val) if pd.notna(val) and val else default
        
        name_col = next((c for c in data_df.columns if 'name' in c.lower()), None)
        email_col = next((c for c in data_df.columns if 'email' in c.lower()), None)
        phone_col = next((c for c in data_df.columns if 'phone' in c.lower()), None)
        id_col = next((c for c in data_df.columns if 'member' in c.lower() and 'id' in c.lower()), None)
        
        name = safe_get(name_col)
        email = safe_get(email_col)
        phone = safe_get(phone_col, '')
        member_id = safe_get(id_col)
        
        phone_display = phone if phone and phone != '' else 'Not available'
        
        return f"""
CONTACT INFORMATION FOR {name.upper()}:
{'=' * 60}
Name: {name}
Email: {email}
Phone: {phone_display}
Member ID: {member_id}
{'=' * 60}
"""
    
    def intelligent_response(self, query):
        if self.current_member is not None:
            return self.answer_with_context(query)
        
        stats = self.data_loader.get_summary_stats()
        
        context = f"""You are a helpful gym member support assistant. 

Current situation: No member is currently selected.

Database stats:
- Total members: {stats.get('total_members', 0)}
- Total orders: {stats.get('total_orders', 0)}

The user asked: "{query}"

If they're asking about a specific member, politely ask them to provide the member's name, email, or ID.
If they're asking general questions about members, answer based on the stats provided.
Be conversational and helpful."""
        
        return self.gemini.get_response(query, context)
    
    def answer_with_context(self, query):
        try:
            data_df = self.data_loader.get_dataframe('data')
            cols = data_df.columns.tolist()
            
            def safe_get(key, default='N/A'):
                val = self.current_member.get(key)
                return str(val) if pd.notna(val) and val else default
            
            member_info = f"Current Member: {safe_get('Name', 'Unknown')}\n"
            for col in cols[:10]:
                value = safe_get(col)
                if value and value != 'N/A' and value != '':
                    member_info += f"- {col}: {value}\n"
            
            email_col = next((c for c in data_df.columns if 'email' in c.lower()), None)
            if email_col:
                email = self.current_member.get(email_col)
                if pd.notna(email) and email:
                    email_str = str(email)
                    
                    # Get orders safely
                    try:
                        orders = self.data_loader.get_member_orders(email_str)
                        if orders is not None and len(orders) > 0:
                            member_info += f"\n- Total Orders: {len(orders)}"
                            
                            amount_col = next((c for c in orders.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
                            if amount_col:
                                orders_copy = orders.copy()
                                orders_copy[amount_col] = pd.to_numeric(orders_copy[amount_col], errors='coerce')
                                total_spent = orders_copy[amount_col].sum()
                                member_info += f"\n- Total Spent: CAD ${total_spent:.2f}"
                    except Exception as e:
                        print(f"Error getting orders: {e}")
                    
                    # Get payments safely
                    try:
                        payments = self.data_loader.get_member_payments(email_str)
                        if payments is not None and len(payments) > 0:
                            member_info += f"\n- Total Payments: {len(payments)}"
                            
                            amount_col = next((c for c in payments.columns if 'amount' in c.lower() and 'processing' not in c.lower()), None)
                            if amount_col:
                                payments_copy = payments.copy()
                                payments_copy[amount_col] = pd.to_numeric(payments_copy[amount_col], errors='coerce')
                                total_paid = payments_copy[amount_col].sum()
                                member_info += f"\n- Total Paid: CAD ${total_paid:.2f}"
                    except Exception as e:
                        print(f"Error getting payments: {e}")
            
            context = f"""You are a helpful gym member support assistant. Answer the user's question about the current member.

{member_info}

User question: "{query}"

Provide a clear, conversational answer based on the information above. If the information isn't available, say so politely."""
            
            return self.gemini.get_response(query, context)
        
        except Exception as e:
            import traceback
            print(f"\nError in answer_with_context: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            return f"I encountered an error: {str(e)}"