
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
import serpapi
import os
from dotenv import load_dotenv, find_dotenv
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph.state import CompiledStateGraph
import re
from urllib.parse import urlparse



load_dotenv()
open_api_key = os.getenv("OPENAI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY") 
print(f"SERPAPI_API_KEY...",SERPAPI_API_KEY)

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", api_key=open_api_key)





class AgentState(MessagesState):
    # messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage]], operator.add]
    budget: float
    interests: List[str]
    companions: int
    city: List[str]
    days: int
    travel_date: str
    itinerary: List[dict]  



class HotelsInput(BaseModel):
    q: str = Field(description='Location of the hotel')
    check_in_date: str = Field(description='Check-in date. The format is YYYY-MM-DD. e.g. 2024-06-22')
    check_out_date: str = Field(description='Check-out date. The format is YYYY-MM-DD. e.g. 2024-06-28')
    sort_by: Optional[str] = Field(8, description='Parameter is used for sorting the results. Default is sort by highest rating')
    adults: Optional[int] = Field(1, description='Number of adults. Default to 1.')
    children: Optional[int] = Field(0, description='Number of children. Default to 0.')
    rooms: Optional[int] = Field(1, description='Number of rooms. Default to 1.')
    hotel_class: Optional[str] = Field(
        None, description='Parameter defines to include only certain hotel class in the results. for example- 2,3,4')


class HotelsInputSchema(BaseModel):
    params: HotelsInput


def extract_booking_url(hotel_data):
    """
    Extract actual booking URL from hotel data, avoiding SerpAPI internal URLs
    """
  
    url_fields = [
        'booking_url',
        'url',
        'link',
        'website',
        'direct_url',
        'hotel_url'
    ]
    
 
    for field in url_fields:
        url = hotel_data.get(field)
        if url and is_valid_booking_url(url):
            return url
    
  
    if 'booking' in hotel_data and isinstance(hotel_data['booking'], dict):
        for field in url_fields:
            url = hotel_data['booking'].get(field)
            if url and is_valid_booking_url(url):
                return url
    
  
    offers = hotel_data.get('offers', [])
    if offers and isinstance(offers, list):
        for offer in offers[:3]: 
            for field in url_fields:
                url = offer.get(field)
                if url and is_valid_booking_url(url):
                    return url
    
   
    hotel_name = hotel_data.get('name', '')
    location = hotel_data.get('location', '') or hotel_data.get('address', '')
    
    if hotel_name:
   
        return create_direct_booking_url(hotel_name, location)
    
    return None

def create_direct_booking_url(hotel_name, location=""):
    """
    Create direct booking URLs prioritizing Pakistani booking platforms first
    """
   
    clean_name = hotel_name.replace(' ', '+').replace('&', 'and')
    clean_location = location.replace(' ', '+').replace(',', '') if location else ""
    
   
    booking_platforms = [
        {
            'name': 'Sastaticket',
            'url': f"https://www.sastaticket.pk/hotels/search?destination={clean_location}&checkin=2025-05-31&checkout=2025-06-07"
        },
        {
            'name': 'FlyPakistan',
            'url': f"https://flypakistan.pk/hotels?destination={clean_name}&location={clean_location}"
        },
        {
            'name': 'Booking.com',
            'url': f"https://www.booking.com/searchresults.html?ss={clean_name}+{clean_location}&checkin=2025-05-31&checkout=2025-06-07"
        },
        {
            'name': 'Agoda',
            'url': f"https://www.agoda.com/search?city=&searchText={clean_name}&checkIn=2025-05-31&checkOut=2025-06-07"
        },
        {
            'name': 'Hotels.com',
            'url': f"https://www.hotels.com/search.do?q-destination={clean_name}+{clean_location}&q-check-in=2025-05-31&q-check-out=2025-06-07"
        },
        {
            'name': 'Expedia',
            'url': f"https://www.expedia.com/Hotel-Search?destination={clean_name}+{clean_location}&startDate=2025-05-31&endDate=2025-06-07"
        }
    ]
    
   
    return booking_platforms[0]['url']

def get_multiple_booking_options(hotel_name, location=""):
    """
    Get multiple booking platform URLs prioritizing Pakistani sites
    """
    clean_name = hotel_name.replace(' ', '+').replace('&', 'and')
    clean_location = location.replace(' ', '+').replace(',', '') if location else ""
    
    return {
         'sastaticket': f"https://www.sastaticket.pk/hotels/search?destination={clean_location}&checkin=2025-05-31&checkout=2025-06-07",
        'flypakistan': f"https://flypakistan.pk/hotels?destination={clean_name}&location={clean_location}",
        'booking_com': f"https://www.booking.com/searchresults.html?ss={clean_name}+{clean_location}&checkin=2025-05-31&checkout=2025-06-07",
        'agoda': f"https://www.agoda.com/search?searchText={clean_name}&checkIn=2025-05-31&checkOut=2025-06-07",
        'hotels_com': f"https://www.hotels.com/search.do?q-destination={clean_name}+{clean_location}&q-check-in=2025-05-31&q-check-out=2025-06-07",
        'expedia': f"https://www.expedia.com/Hotel-Search?destination={clean_name}+{clean_location}&startDate=2025-05-31&endDate=2025-06-07"
    }

def is_valid_booking_url(url):
    """
    Check if URL is a valid booking URL, prioritizing Pakistani sites
    """
    if not url or not isinstance(url, str):
        return False
    
   
    invalid_patterns = [
        'serpapi.com',
        'search.json',
        'property_token=',
        'engine=google_hotels'
    ]
    
    for pattern in invalid_patterns:
        if pattern in url.lower():
            return False
    
   
    valid_domains = [
        'sastaticket.pk',
        'flypakistan.pk',
        'booking.com',
        'expedia.com',
        'hotels.com',
        'agoda.com',
        'priceline.com',
        'kayak.com',
        'trivago.com',
        'hotel.com',
        'google.com',
        'hotelscombined.com'
    ]
    
   
    if any(domain in url.lower() for domain in valid_domains):
        return True
    
   
    if url.startswith(('http://', 'https://')) and '.' in url:
        return True
    
    return False

def process_hotel_data(hotels_list):
    """
    Process hotel data to extract valid booking URLs and clean data
    """
    processed_hotels = []
    
    for hotel in hotels_list:
   
        booking_url = extract_booking_url(hotel)
        
   
        processed_hotel = {
            'name': hotel.get('name', 'Unknown Hotel'),
            'price': hotel.get('rate_per_night', {}).get('extracted_lowest', 0) or hotel.get('price', 0),
            'rating': hotel.get('overall_rating', 0) or hotel.get('rating', 0),
            'reviews': hotel.get('reviews', 0) or hotel.get('review_count', 0),
            'booking_url': booking_url or create_direct_booking_url(hotel.get('name', ''), hotel.get('location', ''))
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels


@tool(args_schema=HotelsInputSchema)
def hotels_finder(params: HotelsInput):
    '''
    Find hotels using the Google Hotels engine with valid booking URLs.
    Returns:
        list: Processed hotel data with valid booking URLs.
    '''
    search_params = {
        'api_key': SERPAPI_API_KEY,
        'engine': 'google_hotels',
        'hl': 'en',
        'gl': 'pk',
        'q': params.q,
        'check_in_date': params.check_in_date,
        'check_out_date': params.check_out_date,
        'currency': 'PKR',
        'adults': params.adults,
        'children': params.children,
        'rooms': params.rooms,
        'sort_by': params.sort_by,
        'hotel_class': params.hotel_class
    }

    search = serpapi.search(search_params)
    results = search.data
    

    raw_hotels = results.get('properties', [])[:5]
    

    processed_hotels = process_hotel_data(raw_hotels)
    
    print(f"Processed {len(processed_hotels)} hotels with valid booking URLs")
    
    return processed_hotels


def clean_hotel_booking_urls(hotel_data_list):
    """
    Clean up hotel data to remove invalid booking URLs and replace with direct booking URLs
    """
    for hotel in hotel_data_list:
        if 'booking_url' in hotel:
            if not is_valid_booking_url(hotel['booking_url']):
                # Replace with direct booking URL
                hotel_name = hotel.get('name', 'hotel')
                location = hotel.get('location', '') or hotel.get('address', '')
                hotel['booking_url'] = create_direct_booking_url(hotel_name, location)
    
    return hotel_data_list


def enhance_hotel_with_booking_options(hotel_data):
    """
    Add multiple booking platform URLs to hotel data
    """
    hotel_name = hotel_data.get('name', '')
    location = hotel_data.get('location', '') or hotel_data.get('address', '')
    
    booking_options = get_multiple_booking_options(hotel_name, location)
    
 
    hotel_data['booking_url'] = booking_options['booking_com']
    
 
    hotel_data['booking_alternatives'] = {
        'agoda': booking_options['agoda'],
        'hotels_com': booking_options['hotels_com'],
        'expedia': booking_options['expedia']
    }
    
    return hotel_data














class ImageSearchInput(BaseModel):
    q: str = Field(description="Search query for the image")
    safe: Optional[str] = Field(default="active", description="Safe search setting: active, moderate, or off")

def is_problematic_url(url):
    """
    Check if URL is from known problematic sources
    """
    if not url:
        return True
    
    problematic_patterns = [
 
        r'lh\d+\.googleusercontent\.com/p/',
        r'drive\.google\.com',
        r'photos\.google\.com',
        
 
        r'\.trvl-media\.com', 
        r'booking\.com.*images',
        r'expedia\.com.*images',
        
 
        r'.*[?&](token|auth|signature|expires)=',
        
 
        r'lh\d+\.googleusercontent\.com.*=s\d+$',
        
        
        r'.*[?&](utm_|fbclid|gclid)',
    ]
    
    for pattern in problematic_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

def filter_reliable_images(image_results, max_images=10):
    """
    Filter image results to exclude problematic URLs and prioritize reliable sources
    """
    reliable_images = []
    
  
    preferred_domains = [
        'upload.wikimedia.org',
        'commons.wikimedia.org',
        'unsplash.com',
        'pixabay.com',
        'pexels.com',
        'flickr.com',
        'staticflickr.com'
    ]
    
  
    for img in image_results:
        if len(reliable_images) >= max_images:
            break
            
        url_candidates = [
            img.get('original'),
            img.get('link'),
            img.get('thumbnail'),
            img.get('source')
        ]
        
        for url in url_candidates:
            if url and not is_problematic_url(url):
                domain = urlparse(url).netloc.lower()
                
             
                if any(pref_domain in domain for pref_domain in preferred_domains):
                    reliable_images.append({"url": url})
                    break
    
   
    if len(reliable_images) < max_images:
        for img in image_results:
            if len(reliable_images) >= max_images:
                break
                
            url_candidates = [
                img.get('original'),
                img.get('link'),
                img.get('thumbnail'),
                img.get('source')
            ]
            
            for url in url_candidates:
                if url and not is_problematic_url(url):
                  
                    if not any(existing['url'] == url for existing in reliable_images):
                        reliable_images.append({"url": url})
                        break
    
    return reliable_images


@tool
def image_finder(q: str, safe: str = "active") -> list:
    '''
    Find reliable images using Google Images via SerpAPI, filtering out problematic URLs.
    Args:
        q: Search query for the image
        safe: Safe search setting (active, moderate, or off)
    Returns:
        list: List of reliable image results with working URLs
    '''
    search_params = {
        "api_key": SERPAPI_API_KEY,
        "engine": "google_images",
        "q": q,
        "safe": safe,
        "hl": "en",
        "gl": "pk",
        "tbm": "isch",  
        "num": "20"    
    }

    search = serpapi.search(search_params)
    results = search.data
    
   
    raw_images = results.get("images_results", [])
    
   
    reliable_images = filter_reliable_images(raw_images, max_images=10)
    
   
    if len(reliable_images) < 5:
        print(f"Only found {len(reliable_images)} reliable images for '{q}', trying broader search...")
        
      
        alt_queries = [f"{q} wallpaper", f"{q} landscape photos", f"{q} tourism photos"]
        
        for alt_q in alt_queries:
            if len(reliable_images) >= 8:
                break
                
            alt_search_params = search_params.copy()
            alt_search_params["q"] = alt_q
            
            alt_search = serpapi.search(alt_search_params)
            alt_results = alt_search.data
            alt_images = alt_results.get("images_results", [])
            
            additional_reliable = filter_reliable_images(
                alt_images, 
                max_images=10-len(reliable_images)
            )
            
          
            for new_img in additional_reliable:
                if not any(existing['url'] == new_img['url'] for existing in reliable_images):
                    reliable_images.append(new_img)
    
    print(f"Found {len(reliable_images)} reliable images for '{q}'")
    return reliable_images








     



def get_system_prompt(state: AgentState):
    return f"""You are a smart travel assistant. Create a detailed itinerary in JSON format considering:
    - Budget: PKR {state['budget']}
    - Travel Interests: {', '.join(state['interests'])}
    - Companions: {state['companions']} people
    - Destination: {state['city']}
    - Duration: {state['days']} days
    - Travel Date: {state['travel_date']}

   IMPORTANT: For each city in the destinations list, you must:
    1. Use hotels_finder tool to get hotel information for EACH city separately
    2. Use image_finder tool to get destination images for EACH city separately
    3. Use image_finder tool to get hotel images for EACH city separately

    For each city ({', '.join(state['city'])}), perform these searches:
    1. Destination images: search for "[City Name] Pakistan tourism photos"
    2. Hotel search: use hotels_finder for each city
    3. Hotel images: search for "[City Name] Pakistan hotels interior rooms"
    
    CRITICAL: Each hotel must have its own unique image. Do NOT reuse the same image URL for different hotels.

    The response should be a valid JSON object with the following structure:
    {{
        "trip_details": {{
            "destination": string,
            "duration": number,
            "travel_date": string,
            "companions": number,
            "budget": number,  # in PKR
            "interests": string[]
        }},

        "destination_images": [
            {{
                "url": string,
            }}
        ],

        "hotel_images": [
                           {{
                              "url": string,
                           }}
        ],

        "daily_itinerary": [
            {{
                "day": number,
                "date": string,
                "day_title": string,  # e.g., "Cultural Tour", "Arrival Day", "Adventure Day"
                "description": string,  # Brief description of the day's theme and activities
                "hotel": {{
                    "name": string,
                    "price": number,  # in PKR
                    "rating": number,
                    "reviews": number,
                    "booking_url": string,
                    "hotel_image": string  # This should be unique for each hotel
                }},
                }},
                "transportation": {{
                    "type": string,
                    "cost": number  # in PKR
                }},
                "meals": [
                    {{
                        "type": string,
                        "venue": string,
                        "cost": number  # in PKR
                    }}
                ],
                "activities": [
                    {{
                        "name": string,
                        "description": string,
                        "cost": number,  # in PKR
                    }}
                ],
            }}
        ],

        "total_cost": number,  # in PKR
        "remaining_budget": number  # in PKR
    }}

    Instructions:
    1. Use image_finder to get 8-10 high-quality images of destination:{state['city']} and "{', '.join(state['city'])} hotel images.
    2. Include destination images in the destination_images array
    3. Include hotel images in the hotel_images array
    4. Ensure all image URLs are valid and accessible

    For each day:
    1. Provide a meaningful day_title that describes the theme (e.g., "Cultural Tour", "Adventure Day")
    2. Include a brief description explaining the day's focus and highlights


    In the cost_summary:
    1. Calculate the total trip cost in PKR
    2. Show the remaining budget from the original amount in PKR
    """


tools = [hotels_finder,image_finder]
llm_with_tools = llm.bind_tools(tools)

def assistant(state: AgentState)->AgentState:
    system_prompt = SystemMessage(content=get_system_prompt(state))
    print("state",[system_prompt] + state["messages"])
    return {"messages": [llm_with_tools.invoke([system_prompt] + state["messages"])]}


builder: StateGraph = StateGraph(AgentState)


builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))


builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")
graph: CompiledStateGraph = builder.compile()