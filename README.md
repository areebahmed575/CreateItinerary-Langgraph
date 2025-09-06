# Travel Itinerary Agent 🌍

An intelligent travel planning agent that creates detailed itineraries with hotels, images, and activities for Pakistan destinations using AI and real-time data.

## Features ✨

- **Smart Itinerary Generation**: AI-powered travel planning based on budget, interests, and preferences
- **Hotel Integration**: Real-time hotel search with booking URLs from multiple platforms
- **Image Curation**: Automatic destination and hotel image sourcing with reliability filtering
- **Multi-City Support**: Plan trips across multiple Pakistani cities
- **Budget Optimization**: Cost-aware planning with detailed expense breakdowns
- **Pakistani Focus**: Prioritizes local booking platforms and PKR currency

## Tech Stack 🛠️

- **Framework**: LangGraph for agent orchestration
- **LLM**: OpenAI GPT-4o-mini via LangChain
- **APIs**: SerpAPI for search functionality
- **Backend**: FastAPI with Uvicorn
- **Language**: Python 3.8+
- **Data Validation**: Pydantic models

## Project Structure 📁

```
prototype/
├── agent.py           # Core agent logic and tools
├── main.py           # FastAPI application entry point
├── router.py         # API routing (if exists)
├── requirements.txt  # Python dependencies
├── .env.example     # Environment variables template
├── Procfile         # Heroku deployment configuration
├── langgraph.json   # LangGraph configuration
└── itenatory.ipynb  # Jupyter notebook for testing
```

## Installation 🚀

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- SerpAPI key

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd prototype
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   SERPAPI_API_KEY=your_serpapi_key
   GOOGLE_API_KEY=your_google_api_key (optional)
   LANGCHAIN_API_KEY=your_langchain_key (optional)
   LANGCHAIN_TRACING_V2=true (optional)
   LANGCHAIN_PROJECT=your_project_name (optional)
   LANGSMITH_API_KEY=your_langsmith_key (optional)
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --host=0.0.0.0 --port=8001 --reload
   ```

## API Usage 📊

### Agent State Structure

The agent expects an `AgentState` object with the following parameters:

```python
{
    "budget": 50000,              # Budget in PKR
    "interests": ["culture", "adventure"],  # Travel interests
    "companions": 2,              # Number of people
    "city": ["Lahore", "Karachi"], # Destination cities
    "days": 5,                   # Trip duration
    "travel_date": "2025-06-01", # Travel start date
    "messages": []               # Chat history
}
```

### Response Format

The agent returns a detailed JSON itinerary:

```json
{
  "trip_details": {
    "destination": "Lahore, Karachi",
    "duration": 5,
    "travel_date": "2025-06-01",
    "companions": 2,
    "budget": 50000,
    "interests": ["culture", "adventure"]
  },
  "destination_images": [
    {"url": "https://example.com/destination1.jpg"}
  ],
  "hotel_images": [
    {"url": "https://example.com/hotel1.jpg"}
  ],
  "daily_itinerary": [
    {
      "day": 1,
      "date": "2025-06-01",
      "day_title": "Arrival Day",
      "description": "Welcome to Lahore...",
      "hotel": {
        "name": "Hotel Example",
        "price": 8000,
        "rating": 4.2,
        "reviews": 150,
        "booking_url": "https://booking-url",
        "hotel_image": "https://hotel-image-url"
      },
      "transportation": {
        "type": "Taxi",
        "cost": 1500
      },
      "meals": [
        {
          "type": "Dinner",
          "venue": "Local Restaurant",
          "cost": 2000
        }
      ],
      "activities": [
        {
          "name": "City Tour",
          "description": "Explore historical sites",
          "cost": 3000
        }
      ]
    }
  ],
  "total_cost": 45000,
  "remaining_budget": 5000
}
```

## Support 💬

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section
- Review the LangGraph and LangChain documentation

---

**Note**: This agent is optimized for Pakistani destinations and uses PKR currency. Modify the system prompts and booking platforms for other regions.