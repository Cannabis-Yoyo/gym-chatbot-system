import sys
import os
from config import Config
from data_loader import DataLoader
from member_bot import MemberBot
from sales_bot import SalesBot
from insights_bot import InsightsBot
from gym_chatbot_system.logging_utils import logger

class GymChatbotSystem:
    def __init__(self):
        self.data_loader = None
        self.member_bot = None
        self.sales_bot = None
        self.insights_bot = None
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_welcome_banner(self):
        self.clear_screen()
        print("\n" + "=" * 60)
        print("           GYM CHATBOT MANAGEMENT SYSTEM")
        print("                   Version " + Config.get_app_version())
        print("=" * 60)
        print()
    
    def initialize(self):
        self.show_welcome_banner()
        print("Initializing system...\n")
        
        try:
            # Validate configuration
            Config.validate()
            logger.info("Configuration validated successfully")
            
            # Show data folder location
            print(f"Data Folder: {Config.get_data_folder()}")
            print()
            
            # Load data with silent auto-detection of new files
            self.data_loader = DataLoader()
            
            if not self.data_loader.load_all_data():
                print("\n⚠ WARNING: No data files found!")
                print(f"Please add data files (.xlsx, .xls, .csv) to:")
                print(f"  {Config.get_data_folder()}")
                print("\nPress Enter to continue anyway, or close the app to add files...")
                input()
                logger.warning("No data files loaded - continuing with empty database")
            else:
                print("\n✓ Datasets loaded:")
                for info in self.data_loader.get_dataset_info():
                    print(f"  • {info}")
                print()
            
            # Initialize bots
            self.member_bot = MemberBot(self.data_loader)
            self.sales_bot = SalesBot(self.data_loader)
            self.insights_bot = InsightsBot(self.data_loader)
            
            logger.info("System initialized successfully")
            print("✓ System initialized successfully!\n")
            
            input("Press Enter to continue...")
            return True
            
        except Exception as e:
            logger.error_with_trace(e, "System initialization")
            print(f"\n✗ Initialization failed: {e}")
            print("\nPlease check the debug log for details:")
            print(f"  {logger.get_log_path()}")
            print("\nPress Enter to exit...")
            input()
            return False
    
    def show_menu(self):
        self.clear_screen()
        print("\n" + "=" * 60)
        print("           MAIN MENU - Select a Chatbot")
        print("=" * 60)
        print("\n1  Member Support Bot")
        print("   Find members, check contacts, view activity")
        print("\n2  Sales & Orders Bot")
        print("   Track orders, check payments, view sales")
        print("\n3  Data Insights Bot")
        print("   Analytics, trends, and reports")
        print("\n4  Show System Stats")
        print("\n5  View Debug Log (Admin)")
        print("\n0  Exit System")
        print("\n" + "=" * 60)
    
    def show_stats(self):
        stats = self.data_loader.get_summary_stats()
        
        self.clear_screen()
        print("\n" + "=" * 60)
        print("              SYSTEM STATISTICS")
        print("=" * 60)
        print()
        
        if 'total_members' in stats:
            print(f"Total Members:      {stats['total_members']:,}")
        
        if 'total_orders' in stats:
            print(f"Total Orders:       {stats['total_orders']:,}")
        
        if 'paid_orders' in stats:
            print(f"Paid Orders:        {stats['paid_orders']:,}")
        
        if 'total_revenue' in stats:
            print(f"Total Revenue:      CAD ${stats['total_revenue']:,.2f}")
        
        print()
        print(f"Data Folder:        {Config.get_data_folder()}")
        print(f"Datasets Loaded:    {len(self.data_loader.get_all_dataframes())}")
        
        print("\n" + "=" * 60)
        input("\nPress Enter to continue...")
    
    def view_debug_log(self):
        self.clear_screen()
        print("\n" + "=" * 60)
        print("           DEBUG LOG VIEWER (ADMIN ONLY)")
        print("=" * 60)
        print()
        
        log_path = logger.get_log_path()
        
        if not os.path.exists(log_path):
            print("No log file found yet.")
        else:
            try:
                file_size = os.path.getsize(log_path) / 1024  # KB
                print(f"Log File: {log_path}")
                print(f"Size:     {file_size:.2f} KB")
                print("\n" + "=" * 60)
                print("RECENT LOG ENTRIES (Last 30 lines):")
                print("=" * 60 + "\n")
                
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-30:] if len(lines) > 30 else lines
                    
                    for line in recent_lines:
                        print(line.rstrip())
                
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        print("\n" + "=" * 60)
        print("\nOptions:")
        print("1. Open full log file in notepad")
        print("2. Return to main menu")
        
        choice = input("\nEnter choice (1-2): ").strip()
        
        if choice == '1' and os.path.exists(log_path):
            try:
                os.system(f'notepad "{log_path}"')
            except:
                print("Could not open notepad")
                input("Press Enter to continue...")
    
    def run(self):
        if not self.initialize():
            return
        
        logger.info("Application main loop started")
        
        while True:
            try:
                self.show_menu()
                
                choice = input("\nEnter your choice (0-5): ").strip()
                
                if choice == '1':
                    logger.info("User selected: Member Support Bot")
                    self.member_bot.start()
                
                elif choice == '2':
                    logger.info("User selected: Sales & Orders Bot")
                    self.sales_bot.start()
                
                elif choice == '3':
                    logger.info("User selected: Data Insights Bot")
                    self.insights_bot.start()
                
                elif choice == '4':
                    logger.info("User selected: Show System Stats")
                    self.show_stats()
                
                elif choice == '5':
                    logger.info("Admin viewing debug log")
                    self.view_debug_log()
                
                elif choice == '0':
                    self.clear_screen()
                    print("\n" + "=" * 60)
                    print("     Thank you for using Gym Chatbot System!")
                    print("=" * 60 + "\n")
                    logger.info("Application closed by user")
                    input("Press Enter to exit...")
                    sys.exit(0)
                
                else:
                    print("\n✗ Invalid choice. Please select 0-5.")
                    input("Press Enter to continue...")
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                logger.info("Application interrupted by user (Ctrl+C)")
                sys.exit(0)
            
            except Exception as e:
                logger.error_with_trace(e, "Main loop")
                print(f"\n✗ Unexpected error: {e}")
                print("\nCheck debug log for details:")
                print(f"  {logger.get_log_path()}")
                input("\nPress Enter to continue...")

def main():
    try:
        system = GymChatbotSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\nSystem interrupted. Goodbye!")
        logger.info("Application terminated")
        sys.exit(0)
    except Exception as e:
        logger.error_with_trace(e, "Fatal error in main")
        print(f"\n✗ Fatal error: {e}")
        print(f"\nCheck debug log: {logger.get_log_path()}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()