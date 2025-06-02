# 🔧 Troubleshooting Guide

This guide helps you resolve common issues when running the Holiday Destinations Generator.

## 🚨 Common Issues and Solutions

### 1. ModuleNotFoundError: No module named 'src'

**Problem**: When running `streamlit run src/ui/streamlit_app.py`, you get:
```
ModuleNotFoundError: No module named 'src'
```

**Root Cause**: Python doesn't know where to find the `src` module because the current directory isn't in the Python path.

**💡 Solutions** (in order of preference):

#### Option A: Use the Python Startup Script (Recommended)
```bash
python start_app.py
```
This automatically configures the Python path and validates your setup.

#### Option B: Use Platform-Specific Scripts
**Windows:**
```cmd
run_app.bat
```

**Unix/Linux/macOS:**
```bash
./run_app.sh
```

#### Option C: Manual Python Path Setup
**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = $PWD
streamlit run src/ui/streamlit_app.py
```

**Windows (Command Prompt):**
```cmd
set PYTHONPATH=%cd%
streamlit run src/ui/streamlit_app.py
```

**Unix/Linux/macOS:**
```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
streamlit run src/ui/streamlit_app.py
```

#### Option D: Python Code Solution
```python
import sys
import os
sys.path.insert(0, os.getcwd())
# Now imports will work
```

### 2. Missing Dependencies

**Problem**: 
```
ImportError: No module named 'streamlit'
ModuleNotFoundError: No module named 'openai'
```

**Solution**:
```bash
pip install -r requirements.txt
```

If you don't have `pip`, install it first:
```bash
# Windows
python -m ensurepip --upgrade

# macOS
python3 -m ensurepip --upgrade

# Ubuntu/Debian
sudo apt install python3-pip
```

### 2.1. Streamlit Badge Compatibility Error

**Problem**:
```
AttributeError: module 'streamlit' has no attribute 'badge'
```

**Root Cause**: Your Streamlit version is older than 1.29.0, which doesn't include the `st.badge()` function.

**💡 Solutions**:

#### Option A: Quick Fix Script (Recommended)
```bash
python fix_streamlit.py
```

#### Option B: Manual Upgrade
```bash
pip install --upgrade streamlit>=1.29.0
```

#### Option C: Full Requirements Update
```bash
pip install --upgrade -r requirements.txt
```

**Note**: The application includes compatibility fallbacks, but upgrading Streamlit is recommended for the best experience.

### 3. OpenAI API Key Issues

**Problem**: 
```
ValueError: OpenAI API key is required
```

**Solutions**:

#### Option A: Create API Key File (Recommended)
```bash
echo "your-api-key-here" > api_key.txt
```

#### Option B: Environment Variable
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Unix/Linux/macOS
export OPENAI_API_KEY=your-api-key-here
```

#### Option C: .env File
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

**Verify your API key**:
```bash
python -c "from src.config.settings import settings; print('API Key configured:', bool(settings.openai_api_key))"
```

### 4. Redis Connection Warnings

**Problem**:
```
Redis not available, caching disabled
```

**Explanation**: This is a warning, not an error. The app automatically falls back to disk caching.

**To Enable Redis** (optional):

#### Windows:
1. Download Redis from https://redis.io/download
2. Install and start Redis service
3. The app will automatically detect and use it

#### macOS:
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian:
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

### 5. Port Already in Use

**Problem**:
```
OSError: [Errno 48] Address already in use
```

**Solutions**:

#### Option A: Use Different Port
```bash
streamlit run src/ui/streamlit_app.py --server.port 8502
```

#### Option B: Kill Process Using Port 8501
**Windows:**
```cmd
netstat -ano | findstr :8501
taskkill /PID <PID_NUMBER> /F
```

**Unix/Linux/macOS:**
```bash
lsof -ti:8501 | xargs kill -9
```

### 6. Fine-Tuning Issues

**Problem**: Fine-tuning fails or times out

**Common Causes & Solutions**:

#### Rate Limits
- **Wait**: Respect OpenAI's rate limits
- **Verify**: Check your OpenAI account usage and limits

#### Insufficient Credits
- **Check**: Verify your OpenAI account balance
- **Add**: Add credits to your OpenAI account

#### Network Issues
- **Check**: Ensure stable internet connection
- **Retry**: Wait a few minutes and try again

#### API Key Permissions
- **Verify**: Ensure your API key has fine-tuning permissions
- **Contact**: Contact OpenAI support if needed

### 7. Performance Issues

**Problem**: Slow response times or high resource usage

**Solutions**:

#### Enable Redis Caching
Follow the Redis setup instructions above.

#### Reduce Concurrent Requests
Adjust the `max_retries` and `retry_delay` in your configuration.

#### Use Fine-Tuned Model
Fine-tuned models often respond faster for domain-specific queries.

### 8. Docker Issues

**Problem**: Docker container won't start or build

**Solutions**:

#### Build Issues
```bash
# Clean build
docker system prune -a
docker-compose build --no-cache
```

#### Environment Variables
```bash
# Pass API key to container
docker run -e OPENAI_API_KEY=your-key -p 8501:8501 holiday-destinations-generator
```

#### Port Conflicts
```bash
# Use different port
docker run -p 8502:8501 holiday-destinations-generator
```

## 🛠️ Diagnostic Commands

### Check Python Setup
```bash
python --version
python -c "import sys; print('Python path:', sys.path)"
```

### Check Dependencies
```bash
python -c "import streamlit, openai, langchain; print('All dependencies OK')"
```

### Check Configuration
```bash
python -c "from src.config.settings import settings; print('Config OK, API key:', bool(settings.openai_api_key))"
```

### Test Fine-Tuning System
```bash
python -c "from src.core.fine_tuning import FineTuningManager; print('Fine-tuning system OK')"
```

## 📞 Getting Help

If you're still experiencing issues:

1. **Check Logs**: Look for detailed error messages in the console output
2. **Search Issues**: Check existing GitHub issues for similar problems
3. **Create Issue**: Open a new GitHub issue with:
   - Your operating system
   - Python version
   - Full error message
   - Steps to reproduce
4. **Contact Support**: For urgent issues, contact the maintainers

## 💡 Prevention Tips

1. **Use Virtual Environment**: Isolate dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix/Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Keep Dependencies Updated**: Regularly update packages
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Monitor API Usage**: Keep track of your OpenAI API usage and limits

4. **Backup Configuration**: Save your API keys and settings securely

5. **Use Recommended Startup Method**: Always use `python start_app.py` for best results

---

**Remember**: Most issues are related to Python path configuration or missing dependencies. The startup scripts handle these automatically! 🚀 