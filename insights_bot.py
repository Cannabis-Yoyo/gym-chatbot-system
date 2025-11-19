from gemini_bot import GeminiBot
from data_loader import DataLoader
import pandas as pd

class InsightsBot:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.gemini = GeminiBot()
        self.conversation_history = []
    
    def start(self):
        print("\n" + "=" * 60)
        print("DATA INSIGHTS BOT")
        print("=" * 60)
        print("Ask me anything about your business analytics in natural language")
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
    
    def understand_intent_with_ai(self, query):
        context = f"""Analyze this user query about business insights/analytics and determine the intent. Return ONLY the intent name.

Available intents:
- comprehensive_overview: User wants general business overview, overall insights, or summary
- member_analytics: User wants member statistics, member insights, or customer analytics
- revenue_analytics: User wants revenue, income, earnings, or financial information
- growth_metrics: User wants growth trends, progress, or performance over time
- activity_metrics: User wants activity, engagement, retention, or usage stats
- acquisition_sources: User wants to know where members come from
- payment_methods: User wants payment method breakdown
- top_performers: User wants top members, best customers, or high spenders
- general_question: General analytical question

User query: "{query}"

Return only one word - the intent name."""
        
        intent = self.gemini.get_response(context, "").strip().lower()
        return intent
    
    def process_query(self, query):
        self.conversation_history.append(query)
        
        intent = self.understand_intent_with_ai(query)
        
        if 'comprehensive' in intent or 'overview' in intent:
            return self.get_comprehensive_insights()
        
        if 'member' in intent:
            return self.get_member_insights()
        
        if 'revenue' in intent:
            return self.get_revenue_insights()
        
        if 'growth' in intent:
            return self.get_growth_metrics()
        
        if 'activity' in intent:
            return self.get_activity_metrics()
        
        if 'acquisition' in intent or 'sources' in intent:
            return self.get_member_sources()
        
        if 'payment_methods' in intent:
            return self.get_payment_analysis()
        
        if 'top' in intent or 'performers' in intent:
            return self.get_top_members()
        
        return self.intelligent_response(query)
    
    def get_comprehensive_insights(self):
        stats = self.data_loader.get_summary_stats()
        data_df = self.data_loader.get_dataframe('data')
        orders_df = self.data_loader.get_dataframe('orders')
        
        info = f"""
BUSINESS OVERVIEW:
{'=' * 60}

MEMBERSHIP:
Total Members: {stats.get('total_members', 0):,}
"""
        
        if data_df is not None:
            activity_col = next((c for c in data_df.columns if 'activity' in c.lower() and 'date' in c.lower()), None)
            if activity_col:
                data_df[activity_col] = pd.to_datetime(data_df[activity_col], errors='coerce')
                latest_date = data_df[activity_col].max()
                active_30d = len(data_df[data_df[activity_col] >= latest_date - pd.Timedelta(days=30)])
                activity_rate = (active_30d / len(data_df) * 100) if len(data_df) > 0 else 0
                info += f"Active Members (30 days): {active_30d:,} ({activity_rate:.1f}%)\n"
        
        info += f"""
SALES PERFORMANCE:
Total Orders: {stats.get('total_orders', 0):,}
Paid Orders: {stats.get('paid_orders', 0):,}
Conversion Rate: {(stats.get('paid_orders', 0) / stats.get('total_orders', 1) * 100):.1f}%

FINANCIAL:
Total Revenue: CAD ${stats.get('total_revenue', 0):,.2f}
"""
        
        if orders_df is not None:
            amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
            if amount_col:
                orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
                avg_order = orders_df[amount_col].mean()
                info += f"Average Order Value: CAD ${avg_order:.2f}\n"
        
        info += "=" * 60
        
        return info
    
    def get_member_insights(self):
        data_df = self.data_loader.get_dataframe('data')
        
        if data_df is None:
            return "I don't have access to member data right now."
        
        total_members = len(data_df)
        
        source_col = next((c for c in data_df.columns if 'source' in c.lower()), None)
        sources = data_df[source_col].value_counts() if source_col else None
        
        activity_col = next((c for c in data_df.columns if 'activity' in c.lower() and 'date' in c.lower()), None)
        
        active_members = 0
        if activity_col:
            data_df[activity_col] = pd.to_datetime(data_df[activity_col], errors='coerce')
            latest_date = data_df[activity_col].max()
            thirty_days_ago = latest_date - pd.Timedelta(days=30)
            active_members = len(data_df[data_df[activity_col] >= thirty_days_ago])
        
        info = f"""
MEMBER ANALYTICS:
{'=' * 60}
Total Members: {total_members:,}
Active Members (30 days): {active_members:,}
Activity Rate: {(active_members/total_members*100):.1f}%
"""
        
        if sources is not None:
            info += "\nTOP ACQUISITION SOURCES:\n"
            for source, count in sources.head(5).items():
                percentage = (count/total_members)*100
                info += f"{source}: {count:,} members ({percentage:.1f}%)\n"
        
        info += "=" * 60
        
        return info
    
    def get_revenue_insights(self):
        payments_df = self.data_loader.get_dataframe('payments')
        
        if payments_df is None:
            return "I don't have access to payment data right now."
        
        amount_col = next((c for c in payments_df.columns if 'amount' in c.lower() and 'processing' not in c.lower() and 'net' not in c.lower()), None)
        net_col = next((c for c in payments_df.columns if 'net' in c.lower()), None)
        fee_col = next((c for c in payments_df.columns if 'fee' in c.lower()), None)
        status_col = next((c for c in payments_df.columns if 'status' in c.lower()), None)
        
        if amount_col:
            payments_df[amount_col] = pd.to_numeric(payments_df[amount_col], errors='coerce')
            total_revenue = payments_df[amount_col].sum()
            avg_transaction = payments_df[amount_col].mean()
        else:
            total_revenue = 0
            avg_transaction = 0
        
        if net_col:
            payments_df[net_col] = pd.to_numeric(payments_df[net_col], errors='coerce')
            total_net = payments_df[net_col].sum()
        else:
            total_net = 0
        
        if fee_col:
            payments_df[fee_col] = pd.to_numeric(payments_df[fee_col], errors='coerce')
            total_fees = payments_df[fee_col].sum()
        else:
            total_fees = 0
        
        successful = len(payments_df[payments_df[status_col] == 'Successful']) if status_col else 0
        success_rate = (successful / len(payments_df) * 100) if len(payments_df) > 0 else 0
        
        info = f"""
REVENUE ANALYTICS:
{'=' * 60}
Total Revenue: CAD ${total_revenue:,.2f}
Net Revenue: CAD ${total_net:,.2f}
Processing Fees: CAD ${total_fees:,.2f}

Transaction Success Rate: {success_rate:.1f}%
Average Transaction: CAD ${avg_transaction:.2f}
Total Transactions: {len(payments_df):,}
{'=' * 60}
"""
        
        return info
    
    def get_growth_metrics(self):
        data_df = self.data_loader.get_dataframe('data')
        orders_df = self.data_loader.get_dataframe('orders')
        
        if data_df is None:
            return "I don't have access to member data right now."
        
        created_col = next((c for c in data_df.columns if 'created' in c.lower() and 'at' in c.lower()), None)
        
        info = f"""
GROWTH METRICS:
{'=' * 60}
Total Members: {len(data_df):,}
"""
        
        if created_col:
            data_df[created_col] = pd.to_datetime(data_df[created_col], errors='coerce')
            members_by_month = data_df.groupby(data_df[created_col].dt.to_period('M')).size()
            
            info += "\nMEMBER GROWTH (Last 6 Months):\n"
            for period, count in members_by_month.tail(6).items():
                info += f"{period}: +{count} new members\n"
        
        if orders_df is not None:
            date_col = next((c for c in orders_df.columns if 'date' in c.lower() and 'created' in c.lower()), None)
            amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
            
            if date_col and amount_col:
                orders_df[date_col] = pd.to_datetime(orders_df[date_col], errors='coerce')
                orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
                revenue_by_month = orders_df.groupby(orders_df[date_col].dt.to_period('M'))[amount_col].sum()
                
                info += f"\nREVENUE GROWTH (Last 6 Months):\n"
                for period, revenue in revenue_by_month.tail(6).items():
                    info += f"{period}: CAD ${revenue:,.2f}\n"
        
        info += "=" * 60
        
        return info
    
    def get_activity_metrics(self):
        data_df = self.data_loader.get_dataframe('data')
        
        if data_df is None:
            return "I don't have access to member data right now."
        
        activity_col = next((c for c in data_df.columns if 'activity' in c.lower() and 'date' in c.lower()), None)
        
        if activity_col is None:
            return "I don't have activity date information available."
        
        data_df[activity_col] = pd.to_datetime(data_df[activity_col], errors='coerce')
        latest_date = data_df[activity_col].max()
        
        active_7d = len(data_df[data_df[activity_col] >= latest_date - pd.Timedelta(days=7)])
        active_30d = len(data_df[data_df[activity_col] >= latest_date - pd.Timedelta(days=30)])
        active_90d = len(data_df[data_df[activity_col] >= latest_date - pd.Timedelta(days=90)])
        
        total = len(data_df)
        
        info = f"""
ACTIVITY & ENGAGEMENT METRICS:
{'=' * 60}
Total Members: {total:,}

ACTIVE MEMBERS:
Last 7 days: {active_7d:,} ({(active_7d/total*100):.1f}%)
Last 30 days: {active_30d:,} ({(active_30d/total*100):.1f}%)
Last 90 days: {active_90d:,} ({(active_90d/total*100):.1f}%)

RETENTION RATES:
7-day: {(active_7d/total*100):.1f}%
30-day: {(active_30d/total*100):.1f}%
90-day: {(active_90d/total*100):.1f}%
{'=' * 60}
"""
        
        return info
    
    def get_member_sources(self):
        data_df = self.data_loader.get_dataframe('data')
        
        if data_df is None:
            return "I don't have access to member data right now."
        
        source_col = next((c for c in data_df.columns if 'source' in c.lower()), None)
        
        if source_col is None:
            return "I don't have source information available."
        
        sources = data_df[source_col].value_counts()
        
        info = "MEMBER ACQUISITION SOURCES:\n" + "=" * 60 + "\n\n"
        
        for source, count in sources.items():
            percentage = (count/len(data_df))*100
            info += f"{source}: {count:,} members ({percentage:.1f}%)\n"
        
        info += "\n" + "=" * 60
        
        return info
    
    def get_payment_analysis(self):
        payments_df = self.data_loader.get_dataframe('payments')
        
        if payments_df is None:
            return "I don't have access to payment data right now."
        
        method_col = next((c for c in payments_df.columns if 'method' in c.lower()), None)
        amount_col = next((c for c in payments_df.columns if 'amount' in c.lower() and 'processing' not in c.lower()), None)
        
        if method_col is None:
            return "I don't have payment method information available."
        
        methods = payments_df[method_col].value_counts()
        
        info = "PAYMENT METHOD ANALYSIS:\n" + "=" * 60 + "\n\n"
        
        for method, count in methods.items():
            percentage = (count/len(payments_df))*100
            
            if amount_col:
                payments_df[amount_col] = pd.to_numeric(payments_df[amount_col], errors='coerce')
                total_amount = payments_df[payments_df[method_col] == method][amount_col].sum()
                avg_amount = total_amount / count
                info += f"{method}:\n"
                info += f"Transactions: {count:,} ({percentage:.1f}%)\n"
                info += f"Total: CAD ${total_amount:,.2f}\n"
                info += f"Average: CAD ${avg_amount:.2f}\n\n"
            else:
                info += f"{method}: {count:,} transactions ({percentage:.1f}%)\n\n"
        
        info += "=" * 60
        
        return info
    
    def get_top_members(self, limit=10):
        top_members = self.data_loader.get_top_members_by_spending(limit)
        
        if top_members is None:
            return "I couldn't retrieve the top members data right now."
        
        info = f"TOP {limit} MEMBERS BY REVENUE:\n{'=' * 60}\n\n"
        
        for idx, row in top_members.iterrows():
            info += f"{idx + 1}. {row['email']}\n"
            info += f"   Orders: {int(row['order_count'])} | Revenue: CAD ${row['total_spent']:,.2f}\n\n"
        
        info += "=" * 60
        
        return info
    
    def build_comprehensive_context(self):
        stats = self.data_loader.get_summary_stats()
        data_df = self.data_loader.get_dataframe('data')
        orders_df = self.data_loader.get_dataframe('orders')
        payments_df = self.data_loader.get_dataframe('payments')
        
        context = f"""
Business Analytics Summary:

MEMBERS:
- Total Members: {stats.get('total_members', 0):,}
"""
        
        if data_df is not None:
            activity_col = next((c for c in data_df.columns if 'activity' in c.lower() and 'date' in c.lower()), None)
            if activity_col:
                data_df[activity_col] = pd.to_datetime(data_df[activity_col], errors='coerce')
                latest_date = data_df[activity_col].max()
                active_30d = len(data_df[data_df[activity_col] >= latest_date - pd.Timedelta(days=30)])
                context += f"- Active (30 days): {active_30d:,}\n"
            
            source_col = next((c for c in data_df.columns if 'source' in c.lower()), None)
            if source_col:
                top_sources = data_df[source_col].value_counts().head(3)
                context += "\nTop Acquisition Sources:\n"
                for source, count in top_sources.items():
                    context += f"- {source}: {count:,} members\n"
        
        context += f"""
SALES:
- Total Orders: {stats.get('total_orders', 0):,}
- Paid Orders: {stats.get('paid_orders', 0):,}

REVENUE:
- Total Revenue: CAD ${stats.get('total_revenue', 0):,.2f}
"""
        
        if orders_df is not None:
            amount_col = next((c for c in orders_df.columns if 'amount' in c.lower() and 'paid' in c.lower()), None)
            if amount_col:
                orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
                avg_order = orders_df[amount_col].mean()
                context += f"- Average Order Value: CAD ${avg_order:.2f}\n"
        
        if payments_df is not None:
            status_col = next((c for c in payments_df.columns if 'status' in c.lower()), None)
            if status_col:
                success_rate = len(payments_df[payments_df[status_col] == 'Successful']) / len(payments_df) * 100
                context += f"- Payment Success Rate: {success_rate:.1f}%\n"
        
        return context
    
    def intelligent_response(self, query):
        context_data = self.build_comprehensive_context()
        
        context = f"""You are a data analyst for a gym management system. Provide insights based on this data:

{context_data}

User question: "{query}"

Analyze the data, identify trends, and provide actionable insights. Be conversational, specific, and data-driven. If you need more information to give a better answer, ask the user."""
        
        return self.gemini.get_response(query, context)