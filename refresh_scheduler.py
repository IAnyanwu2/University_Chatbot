#!/usr/bin/env python3
"""
Background Cache Refresh Scheduler for GSU CS Chatbot

This script handles scheduled background refreshing of the GSU website cache.
Run this script daily via cron job (Linux/Mac) or Task Scheduler (Windows).

Usage:
    python refresh_scheduler.py

For Windows Task Scheduler:
    - Create a new task
    - Set trigger: Daily at 3:00 AM (off-peak hours)
    - Set action: Start program python.exe with argument refresh_scheduler.py
    - Set start in: C:\Users\Ikean\Chatbot\

For Linux/Mac cron job:
    # Run daily at 3:00 AM
    0 3 * * * /usr/bin/python3 /path/to/chatbot/refresh_scheduler.py

For testing:
    python refresh_scheduler.py --test
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from document_processor import DocumentProcessor

def setup_logging():
    """Setup logging for the scheduler"""
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "refresh_scheduler.log"),
            logging.StreamHandler()  # Also log to console
        ]
    )

def main():
    """Main scheduler function"""
    parser = argparse.ArgumentParser(description="GSU CS Chatbot Cache Refresh Scheduler")
    parser.add_argument('--test', action='store_true', help='Run test refresh (more verbose logging)')
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.test:
        logger.info("🧪 Running test refresh...")
    else:
        logger.info("🔄 Starting scheduled cache refresh...")
    
    try:
        # Initialize document processor
        doc_processor = DocumentProcessor()
        
        # Check current cache status
        cache_info = doc_processor.get_cache_info()
        logger.info(f"Current cache: {cache_info}")
        
        # Perform background refresh
        refresh_result = doc_processor.scheduled_background_refresh()
        
        # Log results
        if refresh_result['status'] == 'success':
            logger.info(f"✅ Refresh completed successfully:")
            logger.info(f"   - Duration: {refresh_result['duration_seconds']} seconds")
            logger.info(f"   - Documents updated: {refresh_result['documents_updated']}")
            logger.info(f"   - URLs scraped: {refresh_result['urls_scraped']}")
        else:
            logger.error(f"❌ Refresh failed:")
            logger.error(f"   - Duration: {refresh_result['duration_seconds']} seconds")
            logger.error(f"   - Error: {refresh_result.get('error', 'Unknown error')}")
            
        # Show refresh history if test mode
        if args.test:
            history = doc_processor.get_refresh_history()
            logger.info(f"Recent refresh history (last {len(history)} attempts):")
            for entry in history[-5:]:  # Show last 5
                status_emoji = "✅" if entry['status'] == 'success' else "❌"
                logger.info(f"   {status_emoji} {entry['timestamp']} - {entry['status']} ({entry['duration_seconds']}s)")
    
    except Exception as e:
        logger.error(f"💥 Scheduler failed with exception: {e}")
        sys.exit(1)
    
    if args.test:
        logger.info("🧪 Test refresh completed")
    else:
        logger.info("🔄 Scheduled refresh completed")

if __name__ == "__main__":
    main()