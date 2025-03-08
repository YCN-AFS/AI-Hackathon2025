from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from travel_scraper_example import TravelokaScraper
import uvicorn
from pyngrok import ngrok, conf

app = FastAPI(
    title="Hotel URL Generator API",
    description="API để tạo URL tìm kiếm khách sạn trên Traveloka",
    version="1.0.0"
)

# Cho phép truy cập từ mọi nguồn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    location: str
    check_in: datetime
    check_out: datetime
    adults: int = 1
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Đà Nẵng",
                "check_in": "2024-03-20",
                "check_out": "2024-03-22",
                "adults": 2
            }
        }

class URLResponse(BaseModel):
    url: str
    params: dict

@app.get("/")
def read_root():
    return {
        "status": "online",
        "endpoints": {
            "generate_url": "/api/v1/generate-url",
            "docs": "/docs"
        }
    }

@app.post("/api/v1/generate-url", response_model=URLResponse)
def generate_url(request: URLRequest):
    try:
        scraper = TravelokaScraper()
        url = scraper.build_hotel_search_url(
            location=request.location,
            check_in=request.check_in,
            check_out=request.check_out,
            adults=request.adults
        )
        
        return URLResponse(
            url=url,
            params={
                "location": request.location,
                "check_in": request.check_in.strftime('%d-%m-%Y'),
                "check_out": request.check_out.strftime('%d-%m-%Y'),
                "adults": request.adults
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Thêm endpoint mới để lấy danh sách khách sạn
@app.post("/api/v1/search-hotels")
def search_hotels(request: dict):
    try:
        scraper = TravelokaScraper()
        hotels = scraper.get_hotels(
            location=request["location"],
            check_in=datetime.fromisoformat(request["check_in"]),
            check_out=datetime.fromisoformat(request["check_out"]),
            adults=request["adults"]
        )
        return {
            "total": len(hotels),
            "hotels": hotels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    # Cấu hình ngrok authtoken
    ngrok.set_auth_token("2u1qQIoOLe6tloBg3zRir1PvRQI_5KTnVgAfziPjh8xQE3rzw")
    
    # Tạo tunnel ngrok
    public_url = ngrok.connect(8000).public_url
    print(f"Ngrok tunnel created: {public_url}")
    print(f"OpenAPI documentation: {public_url}/docs")
    
    # Chạy server
    uvicorn.run("api:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_server() 