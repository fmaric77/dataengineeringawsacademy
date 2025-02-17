from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json

app = FastAPI()

with open('Day4/nobel_prizes.json', 'r') as file:
    nobel_prizes = json.load(file)['prizes']
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Nobel Prize API!",
        "endpoints": {
            "Get Nobel Prizes by Category": "/nobel_prizes/{category}",
            "Get Nobel Prizes by Year": "/nobel_prizes/year/{year}",
            "To test PUT go to": "/docs"
        
        }
    }

@app.get("/nobel_prizes/{category}", response_model=List[Dict[str, Any]])
async def get_nobel_prizes_by_category(category: str):
    filtered_prizes = [prize for prize in nobel_prizes if prize['category'] == category]
    
    if not filtered_prizes:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return filtered_prizes

@app.get("/nobel_prizes/year/{year}", response_model=List[Dict[str, Any]])
async def get_nobel_prizes_by_year(year: str):
    filtered_prizes = [prize for prize in nobel_prizes if prize['year'] == year]
    
    if not filtered_prizes:
        raise HTTPException(status_code=404, detail="Year not found")
    
    return filtered_prizes


class Name(BaseModel):
    first_name: str
    surname: str

@app.put("/nobel_prizes/laureate/{id}", response_model=Dict[str, Any])
async def update_laureate_name(id: str, name: Name):
    for prize in nobel_prizes:
        for laureate in prize.get('laureates', []):
            if laureate['id'] == id:
                laureate['firstname'] = name.first_name
                laureate['surname'] = name.surname
                
                with open('Day4/nobel_prizes.json', 'w') as file:
                    json.dump({"prizes": nobel_prizes}, file, indent=4)

                return laureate
    
    raise HTTPException(status_code=404, detail="Laureate not found")
