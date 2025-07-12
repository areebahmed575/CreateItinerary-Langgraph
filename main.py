from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware
from agent import graph 


class TravelPlanRequest(BaseModel):
    budget: float
    interests: List[str]
    companions: int
    city: str
    days: int
    travel_date: str
    initial_message: str = "Plan my trip to Pakistan"

app = FastAPI(title="Travel Planner API", description="API for generating travel itineraries using Langgraph.")



app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "http://localhost:3000",
        "https://pakigentravel.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.post("/create_itinerary")
async def plan_trip(request: TravelPlanRequest):
    try:
        
        print("Received request:", request.dict())

        initial_state = {
            "messages": [HumanMessage(content=request.initial_message)],
            "budget": request.budget,
            "interests": request.interests,
            "companions": request.companions,
            "city": request.city,
            "days": request.days,
            "travel_date": request.travel_date,
            "itinerary": []  
        }

    
        config = {"configurable": {"thread_id": "1"}}

    
        response = [chunk async for chunk in graph.astream(initial_state, config)]
        
    
        final_response = response[-1]

        print("Generated response:", final_response)
        
        return final_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating itinerary: {str(e)}")

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8001)