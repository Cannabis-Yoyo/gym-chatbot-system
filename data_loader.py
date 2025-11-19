import pandas as pd
import os
import json
from config import Config
from datetime import datetime
from logger import logger

class DataLoader:
    def __init__(self):
        self.data_folder = Config.DATA_FOLDER
        self.csv_cache_folder = Config.CSV_CACHE_FOLDER
        self.last_scan_file = Config.LAST_SCAN_FILE
        self.dataframes = {}
        self.date_columns = {}
        self.file_mappings = {}
        self.file_groups = {}
        
        self.check_for_new_files()
    
    def detect_file_type(self, df, filename):
        """Detect what type of data file this is based on columns"""
        columns_lower = [col.lower() for col in df.columns]
        columns_str = ' '.join(columns_lower)
        filename_lower = filename.lower()
        
        # Check filename first for common patterns
        if 'contact' in filename_lower or ('data' in filename_lower and 'member' not in filename_lower):
            return 'data'
        
        if 'order' in filename_lower and 'item' not in filename_lower:
            return 'orders'
        
        if 'payment' in filename_lower:
            return 'payments'
        
        if 'item' in filename_lower:
            return 'items_purchased'
        
        # Then check columns
        if any(keyword in columns_str for keyword in ['member', 'contact', 'phone', 'subscription']):
            if any(keyword in columns_str for keyword in ['name', 'email']):
                return 'data'
        
        if 'order' in columns_str and 'number' in columns_str:
            if any(keyword in columns_str for keyword in ['payment', 'amount', 'status']):
                return 'orders'
        
        if 'payment' in columns_str:
            if any(keyword in columns_str for keyword in ['amount', 'method', 'transaction', 'stripe']):
                return 'payments'
        
        if 'item' in columns_str and 'order' in columns_str:
            if any(keyword in columns_str for keyword in ['quantity', 'qty', 'purchased']):
                return 'items_purchased'
        
        base_name = os.path.splitext(filename)[0].lower().replace(' ', '_')
        logger.warning(f"Could not auto-detect file type for {filename}, using filename: {base_name}")
        return base_name
    
    def check_for_new_files(self):
        """Silently check for new files and reload if needed"""
        try:
            current_files = set(self.get_all_data_files())
            
            last_scan_info = self.load_last_scan()
            last_files = set(last_scan_info.get('files', []))
            
            new_files = current_files - last_files
            
            if new_files:
                logger.log_data_scan(len(current_files), list(new_files))
            
            self.save_last_scan(list(current_files))
            
        except Exception as e:
            logger.error(f"Error checking for new files: {e}")
    
    def load_last_scan(self):
        """Load last scan information"""
        try:
            if os.path.exists(self.last_scan_file):
                with open(self.last_scan_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'files': [], 'timestamp': None}
    
    def save_last_scan(self, files):
        """Save current scan information"""
        try:
            scan_info = {
                'files': files,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.last_scan_file, 'w') as f:
                json.dump(scan_info, f)
        except Exception as e:
            logger.error(f"Error saving scan info: {e}")
    
    def get_all_data_files(self):
        files = []
        try:
            if not os.path.exists(self.data_folder):
                logger.warning(f"Data folder not found: {self.data_folder}")
                return files
            
            for filename in os.listdir(self.data_folder):
                if filename.endswith(('.xlsx', '.xls', '.csv')):
                    filepath = os.path.join(self.data_folder, filename)
                    if os.path.isfile(filepath):
                        files.append(filename)
        except Exception as e:
            logger.error(f"Error scanning data folder: {e}")
        
        return files
    
    def convert_excel_to_csv(self, excel_file):
        excel_path = os.path.join(self.data_folder, excel_file)
        csv_filename = os.path.splitext(excel_file)[0] + '.csv'
        csv_path = os.path.join(self.csv_cache_folder, csv_filename)
        
        try:
            excel_mtime = os.path.getmtime(excel_path)
            
            if os.path.exists(csv_path):
                csv_mtime = os.path.getmtime(csv_path)
                if csv_mtime >= excel_mtime:
                    return csv_path
            
            df = pd.read_excel(excel_path)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            logger.info(f"Converted: {excel_file} -> {csv_filename}")
            return csv_path
        except Exception as e:
            logger.error(f"Error converting {excel_file}: {e}")
            return None
    
    def detect_and_parse_dates(self, df, filename):
        date_patterns = ['date', 'created', 'activity', 'time', 'datetime']
        date_cols = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in date_patterns):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    date_cols.append(col)
                except:
                    pass
        
        if date_cols:
            self.date_columns[filename] = date_cols
        
        return df
    
    def load_csv_file(self, csv_path, original_filename):
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
            df = self.detect_and_parse_dates(df, original_filename)
            
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('').astype(str)
            
            return df
        except Exception as e:
            logger.error(f"Error loading CSV {csv_path}: {e}")
            return None
    
    def merge_dataframes(self, df_list, file_type):
        """Merge multiple dataframes of the same type"""
        if len(df_list) == 1:
            return df_list[0]
        
        try:
            merged_df = pd.concat(df_list, ignore_index=True)
            
            if file_type == 'data':
                email_col = next((col for col in merged_df.columns if 'email' in col.lower()), None)
                member_id_col = next((col for col in merged_df.columns if 'member' in col.lower() and 'id' in col.lower()), None)
                
                if email_col:
                    merged_df = merged_df.drop_duplicates(subset=[email_col], keep='last')
                elif member_id_col:
                    merged_df = merged_df.drop_duplicates(subset=[member_id_col], keep='last')
            
            elif file_type == 'orders':
                order_col = next((col for col in merged_df.columns if 'order' in col.lower() and 'number' in col.lower()), None)
                if order_col:
                    merged_df = merged_df.drop_duplicates(subset=[order_col], keep='last')
            
            elif file_type == 'payments':
                transaction_col = next((col for col in merged_df.columns if 'transaction' in col.lower() or 'payment_id' in col.lower()), None)
                if transaction_col:
                    merged_df = merged_df.drop_duplicates(subset=[transaction_col], keep='last')
            
            logger.info(f"Merged {len(df_list)} files for type '{file_type}', resulting in {len(merged_df)} total rows")
            return merged_df
            
        except Exception as e:
            logger.error(f"Error merging dataframes for {file_type}: {e}")
            return df_list[0] if df_list else None
    
    def load_all_data(self):
        logger.info("Starting data load process...")
        
        data_files = self.get_all_data_files()
        
        if not data_files:
            logger.warning("No data files found in the data folder!")
            return False
        
        logger.info(f"Found {len(data_files)} data file(s)")
        
        grouped_dfs = {}
        
        for filename in data_files:
            try:
                df = None
                
                if filename.endswith(('.xlsx', '.xls')):
                    csv_path = self.convert_excel_to_csv(filename)
                    if csv_path:
                        df = self.load_csv_file(csv_path, filename)
                
                elif filename.endswith('.csv'):
                    csv_path = os.path.join(self.data_folder, filename)
                    df = self.load_csv_file(csv_path, filename)
                
                if df is not None:
                    file_type = self.detect_file_type(df, filename)
                    
                    if file_type not in grouped_dfs:
                        grouped_dfs[file_type] = []
                        self.file_groups[file_type] = []
                    
                    grouped_dfs[file_type].append(df)
                    self.file_groups[file_type].append(filename)
                    
                    logger.info(f"Loaded: {filename} as '{file_type}' ({len(df)} rows, {len(df.columns)} columns)")
            
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                continue
        
        for file_type, df_list in grouped_dfs.items():
            if len(df_list) > 1:
                logger.info(f"Merging {len(df_list)} files of type '{file_type}'")
                merged_df = self.merge_dataframes(df_list, file_type)
                self.dataframes[file_type] = merged_df
            else:
                self.dataframes[file_type] = df_list[0]
        
        logger.info(f"Data loading complete! Loaded {len(self.dataframes)} dataset type(s)")
        self.log_file_mappings()
        return len(self.dataframes) > 0
    
    def log_file_mappings(self):
        """Log which files were mapped to which types"""
        logger.info("File type mappings:")
        for file_type, filenames in self.file_groups.items():
            if len(filenames) == 1:
                logger.info(f"  {file_type} <- {filenames[0]}")
            else:
                logger.info(f"  {file_type} <- merged from {len(filenames)} files:")
                for filename in filenames:
                    logger.info(f"    - {filename}")
    
    def get_dataframe(self, key):
        return self.dataframes.get(key)
    
    def get_all_dataframes(self):
        return self.dataframes
    
    def query_dataframe(self, key, query_func):
        df = self.get_dataframe(key)
        if df is None:
            return None
        try:
            return query_func(df)
        except Exception as e:
            logger.error(f"Query error on {key}: {e}")
            return None
    
    def search_member(self, query):
        data_df = self.get_dataframe('data')
        if data_df is None:
            return None
        
        query_str = str(query).lower()
        
        search_cols = [col for col in data_df.columns if any(k in col.lower() for k in ['name', 'email', 'member'])]
        
        if not search_cols:
            return None
        
        mask = pd.Series([False] * len(data_df))
        for col in search_cols:
            mask = mask | data_df[col].astype(str).str.lower().str.contains(query_str, na=False, regex=False)
        
        return data_df[mask]
    
    def get_member_orders(self, email):
        orders_df = self.get_dataframe('orders')
        if orders_df is None:
            return None
        
        email_col = None
        for col in orders_df.columns:
            if 'email' in col.lower():
                email_col = col
                break
        
        if email_col is None:
            return None
        
        email_str = str(email).lower()
        mask = orders_df[email_col].astype(str).str.lower() == email_str
        return orders_df[mask].copy()
    
    def get_member_payments(self, email):
        payments_df = self.get_dataframe('payments')
        if payments_df is None:
            return None
        
        email_col = None
        for col in payments_df.columns:
            if 'email' in col.lower():
                email_col = col
                break
        
        if email_col is None:
            return None
        
        email_str = str(email).lower()
        mask = payments_df[email_col].astype(str).str.lower() == email_str
        return payments_df[mask].copy()
    
    def get_orders_by_date_range(self, start_date=None, end_date=None, days=None):
        orders_df = self.get_dataframe('orders')
        if orders_df is None:
            return None
        
        date_col = None
        for col in orders_df.columns:
            if 'date' in col.lower() and 'created' in col.lower():
                date_col = col
                break
        
        if date_col is None:
            for col in orders_df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
        
        if date_col is None:
            return orders_df.copy()
        
        try:
            orders_df[date_col] = pd.to_datetime(orders_df[date_col], errors='coerce')
        except:
            return orders_df.copy()
        
        if days is not None:
            latest_date = orders_df[date_col].max()
            start_date = latest_date - pd.Timedelta(days=days)
            mask = orders_df[date_col] >= start_date
            return orders_df[mask].copy()
        
        if start_date and end_date:
            mask = (orders_df[date_col] >= start_date) & (orders_df[date_col] <= end_date)
            return orders_df[mask].copy()
        elif start_date:
            mask = orders_df[date_col] >= start_date
            return orders_df[mask].copy()
        elif end_date:
            mask = orders_df[date_col] <= end_date
            return orders_df[mask].copy()
        
        return orders_df.copy()
    
    def get_orders_by_month(self, month, year=None):
        orders_df = self.get_dataframe('orders')
        if orders_df is None:
            return None
        
        date_col = None
        for col in orders_df.columns:
            if 'date' in col.lower() and 'created' in col.lower():
                date_col = col
                break
        
        if date_col is None:
            for col in orders_df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
        
        if date_col is None:
            return None
        
        try:
            orders_df[date_col] = pd.to_datetime(orders_df[date_col], errors='coerce')
        except:
            return None
        
        mask = orders_df[date_col].dt.month == month
        filtered = orders_df[mask]
        
        if year:
            mask = filtered[date_col].dt.year == year
            filtered = filtered[mask]
        
        return filtered.copy()
    
    def get_top_members_by_spending(self, limit=10):
        orders_df = self.get_dataframe('orders')
        if orders_df is None:
            return None
        
        email_col = None
        amount_col = None
        
        for col in orders_df.columns:
            if 'email' in col.lower():
                email_col = col
            if 'amount' in col.lower() and 'paid' in col.lower():
                amount_col = col
        
        if email_col is None or amount_col is None:
            return None
        
        try:
            orders_df = orders_df.copy()
            orders_df[amount_col] = pd.to_numeric(orders_df[amount_col], errors='coerce')
        except:
            return None
        
        top_members = orders_df.groupby(email_col).agg({
            email_col: 'first',
            amount_col: ['sum', 'count']
        }).reset_index(drop=True)
        
        top_members.columns = ['email', 'total_spent', 'order_count']
        top_members = top_members.sort_values('total_spent', ascending=False).head(limit)
        
        return top_members
    
    def get_summary_stats(self):
        stats = {}
        
        data_df = self.get_dataframe('data')
        if data_df is not None:
            stats['total_members'] = len(data_df)
        
        orders_df = self.get_dataframe('orders')
        if orders_df is not None:
            stats['total_orders'] = len(orders_df)
            
            status_col = None
            for col in orders_df.columns:
                if 'status' in col.lower() and 'payment' in col.lower():
                    status_col = col
                    break
            
            if status_col:
                mask = orders_df[status_col].astype(str) == 'Paid'
                stats['paid_orders'] = mask.sum()
        
        payments_df = self.get_dataframe('payments')
        if payments_df is not None:
            amount_col = None
            for col in payments_df.columns:
                if 'amount' in col.lower() and 'processing' not in col.lower():
                    amount_col = col
                    break
            
            if amount_col:
                try:
                    payments_df = payments_df.copy()
                    payments_df[amount_col] = pd.to_numeric(payments_df[amount_col], errors='coerce')
                    stats['total_revenue'] = payments_df[amount_col].sum()
                except:
                    pass
        
        return stats
    
    def get_dataset_info(self):
        """Return information about loaded datasets including merged files"""
        info = []
        for key, df in self.dataframes.items():
            file_list = self.file_groups.get(key, [key])
            if len(file_list) == 1:
                info.append(f"{file_list[0]} ({key}): {len(df)} rows, {len(df.columns)} columns")
            else:
                info.append(f"{key} (merged from {len(file_list)} files): {len(df)} rows, {len(df.columns)} columns")
                for filename in file_list:
                    info.append(f"  ↳ {filename}")
        return info