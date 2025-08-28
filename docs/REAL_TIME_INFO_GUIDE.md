# Real-Time Information Capabilities - User Guide (v1.5.4)

## 🎯 Enhanced Real-Time Information Access

The Claude-AGI system now supports **comprehensive real-time information capabilities** including web search, news access, and advanced query processing!

### ✅ System Time & Date Queries

You can now ask Claude for current system information:

- **"What time is it?"** 
- **"What's the current time?"**
- **"What date is it?"**
- **"What day is it today?"**

**Example Response:**
```
The current time is 2025-08-27 23:24:08 on Wednesday. Today's date is 2025-08-27.
```

### ✅ **NEW v1.5.4** - Web Search & Information Access

Ask Claude about current events, search for information, and get real-time news:

- **"What's happening in the news today?"**
- **"Search for information about AI developments"**
- **"What are the latest tech trends?"**
- **"Find news about space exploration"**

**Example Response:**
```
Based on current web search results, here are the latest AI developments:
- Major breakthrough in large language models announced by leading tech companies
- New research in autonomous systems showing significant progress
- AI safety frameworks being implemented across the industry
```

### ✅ Weather Information Queries

Ask Claude about weather conditions anywhere in the world:

- **"What's the weather in New York?"**
- **"Tell me the temperature in London"**
- **"What's the forecast for Tokyo?"**
- **"Is it raining in Seattle?"**

**Example Response:**
```
The weather in New York, US is currently clear skies with a temperature of 22°C 
(feels like 24°C). The humidity is 65%.
```

## 🔧 Setup Instructions

### System Time (Works Immediately)
- ✅ No setup required - works out of the box
- ✅ Uses local system clock for accurate time/date

### **NEW v1.5.4** - Web Search & Information (Requires API Key)

1. **Get API access** from [Brave Search API](https://brave.com/search/api/) or configure alternative search providers
2. **Set the environment variable:**
   ```bash
   export BRAVE_SEARCH_API_KEY=your_api_key_here
   ```
3. **Run the TUI:**
   ```bash
   python claude-agi.py  # Enhanced version with real-time info
   ```

### Weather Information (Requires API Key)

1. **Get a free API key** from [OpenWeatherMap](https://openweathermap.org/api)
2. **Set the environment variable:**
   ```bash
   export OPENWEATHERMAP_API_KEY=your_api_key_here
   ```
3. **Run the TUI:**
   ```bash
   python claude-agi.py
   ```

### Without Weather API Key
If you don't have an API key, Claude will respond with:
```
I couldn't get weather information: Weather API key not configured. 
Please set OPENWEATHERMAP_API_KEY environment variable.
```

## 🧪 Testing

Run the test script to verify functionality:

```bash
python tests/test_realtime_info.py
```

This will test:
- ✅ System time retrieval
- ✅ Weather API integration (if configured)  
- ✅ Query pattern recognition
- ✅ Normal query handling

## 🔍 How It Works

### Intelligent Query Classification
The system automatically detects when you're asking for real-time information:

1. **Time Pattern Detection:** Recognizes phrases like "what time", "current date"
2. **Weather Pattern Detection:** Recognizes phrases like "weather", "temperature", "forecast"
3. **Location Extraction:** Automatically extracts locations from weather queries
4. **Smart Routing:** System info queries → WebExplorer service, others → AI conversation

### Technical Implementation
- **Enhanced WebExplorer Service:** Added secure HTTP client with aiohttp
- **Query Preprocessing:** Intercepts system info requests before AI processing
- **Secure API Integration:** Proper error handling and rate limiting
- **Graceful Fallback:** Falls back to normal AI responses when info unavailable

## 🎮 Try It Out!

Start the TUI and try these example queries:

```bash
python claude-agi.py
```

**In the conversation pane, type:**
- `What time is it right now?`
- `What's the weather in your city?` 
- `Tell me today's date`
- `Is it sunny in Miami?`

## 🛠️ Troubleshooting

### Weather Queries Not Working?
- Check API key is set: `echo $OPENWEATHERMAP_API_KEY`
- Verify API key is valid at [OpenWeatherMap](https://openweathermap.org/api)
- Check internet connection

### Time Queries Not Working?
- This indicates a system error - check logs for details
- System time should always work as it uses local clock

### Location Not Recognized?
- Try more specific location names: "New York, NY" instead of just "NY"
- Include country for international locations: "Paris, France"

## 🔒 Security & Privacy

- **API Keys:** Stored securely in environment variables, never logged
- **HTTP Requests:** Use secure aiohttp client with proper timeout handling
- **Error Handling:** Comprehensive error handling prevents crashes
- **No Data Storage:** Weather/time data is not permanently stored

## 📋 Summary

This enhancement transforms Claude from responding "I don't have access to real-time information" to providing accurate, current data for system time and weather queries. The implementation maintains security best practices while seamlessly integrating into the existing consciousness system.

**Status:** ✅ **FULLY IMPLEMENTED AND TESTED**