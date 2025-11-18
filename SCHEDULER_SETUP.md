# Windows Task Scheduler Setup for Daily Cache Refresh

## 🕒 Goal: Run cache refresh automatically every day at 3:00 AM

### **Step 1: Open Task Scheduler**
1. Press `Win + R`, type `taskschd.msc`, press Enter
2. OR Search "Task Scheduler" in Start menu

### **Step 2: Create New Task**
1. Click **"Create Task..."** (not "Create Basic Task")
2. Name: `GSU Chatbot Cache Refresh`
3. Description: `Daily background refresh of GSU website content cache`
4. Check: **"Run whether user is logged on or not"**
5. Check: **"Run with highest privileges"**
6. Configure for: **Windows 10/11**

### **Step 3: Set Trigger (Daily at 3 AM)**
1. Click **"Triggers"** tab → **"New..."**
2. Begin the task: **"On a schedule"**
3. Settings: **"Daily"**
4. Start: **3:00:00 AM**
5. Recur every: **1 days**
6. Check: **"Enabled"**
7. Click **"OK"**

### **Step 4: Set Action (Run the Refresh Script)**
1. Click **"Actions"** tab → **"New..."**
2. Action: **"Start a program"**
3. Program/script: `C:\Users\Ikean\Chatbot\run_refresh.bat`
4. Start in: `C:\Users\Ikean\Chatbot`
5. Click **"OK"**

### **Step 5: Configure Settings**
1. Click **"Settings"** tab
2. Check: **"Allow task to be run on demand"**
3. Check: **"Run task as soon as possible after a scheduled start is missed"**
4. If running: **"Do not start a new instance"**
5. Click **"OK"**

### **Step 6: Test the Setup**
1. Right-click your new task → **"Run"**
2. Check `refresh_log.txt` for completion message
3. Check logs in `data/refresh_log.json` for details

---

## 📊 Monitoring Your Scheduled Refresh

### Check if refresh ran successfully:
```bash
python -c "from document_processor import DocumentProcessor; dp = DocumentProcessor(); history = dp.get_refresh_history(); print('Last refresh:', history[-1] if history else 'No refreshes yet')"
```

### Check current cache status:
```bash
python -c "from document_processor import DocumentProcessor; dp = DocumentProcessor(); import json; print(json.dumps(dp.get_cache_info(), indent=2))"
```

### Manual refresh for testing:
```bash
python refresh_scheduler.py
```

---

## 🔧 Troubleshooting

- **Task won't run**: Check user permissions and "Run with highest privileges"
- **Python not found**: Update path in `run_refresh.bat` to full Python path
- **Network issues**: Check logs in `data/refresh_log.json` for error details
- **Cache not updating**: Run manual test with `python refresh_scheduler.py`

---

## 📁 Files Created by Scheduler

- `data/refresh_log.json` - Detailed refresh history and errors
- `refresh_log.txt` - Simple completion timestamps
- `data/scraped_documents.pkl` - Updated cache file
- `data/cache_metadata.json` - Cache status and timing

The system is designed to never fail - if refresh fails, users still get cached data!