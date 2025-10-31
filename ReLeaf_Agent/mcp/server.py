import asyncio
import logging
import os
from typing import Dict, List, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Zoo MCP Server on Cloud Run")

# Zoo animal database
ZOO_ANIMALS = {
    "lions": [
        {
            "name": "Simba",
            "age": 8,
            "gender": "male",
            "enclosure": "African Savanna - Section A",
            "species": "African Lion",
            "weight": "190 kg",
            "special_notes": "Alpha male of the pride"
        },
        {
            "name": "Nala",
            "age": 6,
            "gender": "female", 
            "enclosure": "African Savanna - Section A",
            "species": "African Lion",
            "weight": "130 kg",
            "special_notes": "Mother of two cubs"
        }
    ],
    "polar_bears": [
        {
            "name": "Arctic",
            "age": 12,
            "gender": "male",
            "enclosure": "Polar Paradise - North Pool",
            "species": "Polar Bear",
            "weight": "450 kg",
            "special_notes": "Excellent swimmer, loves playing in water"
        },
        {
            "name": "Snow",
            "age": 9,
            "gender": "female",
            "enclosure": "Polar Paradise - South Pool", 
            "species": "Polar Bear",
            "weight": "280 kg",
            "special_notes": "Recently gave birth to a cub"
        }
    ],
    "elephants": [
        {
            "name": "Dumbo", 
            "age": 25,
            "gender": "male",
            "enclosure": "Elephant Valley - Main Exhibit",
            "species": "African Elephant",
            "weight": "5500 kg",
            "special_notes": "Largest elephant in our zoo"
        },
        {
            "name": "Ellie",
            "age": 18,
            "gender": "female",
            "enclosure": "Elephant Valley - Family Area",
            "species": "African Elephant", 
            "weight": "3200 kg",
            "special_notes": "Very gentle and loves interacting with visitors"
        }
    ],
    "giraffes": [
        {
            "name": "Stretch",
            "age": 7,
            "gender": "male",
            "enclosure": "Giraffe Heights - Tower View",
            "species": "Masai Giraffe",
            "weight": "1200 kg",
            "special_notes": "Tallest animal in the zoo at 5.5 meters"
        }
    ],
    "penguins": [
        {
            "name": "Pip",
            "age": 4,
            "gender": "male",
            "enclosure": "Penguin Cove - Ice Slide Area",
            "species": "Emperor Penguin",
            "weight": "25 kg",
            "special_notes": "Leader of the penguin colony"
        },
        {
            "name": "Pebble",
            "age": 3,
            "gender": "female",
            "enclosure": "Penguin Cove - Ice Slide Area", 
            "species": "Emperor Penguin",
            "weight": "20 kg",
            "special_notes": "Known for her playful personality"
        }
    ]
}


@mcp.tool()
def get_animal_info(animal_type: str) -> List[Dict]:
    animal_type = animal_type.lower().replace(" ", "_")
    if animal_type in ZOO_ANIMALS:
        return ZOO_ANIMALS[animal_type]
    matches = []
    for key, animals in ZOO_ANIMALS.items():
        if animal_type in key or key in animal_type:
            matches.extend(animals)
    if matches:
        return matches
    return []


@mcp.tool()
def get_animal_by_name(name: str) -> Optional[Dict]:
    name = name.lower()
    for _, animals in ZOO_ANIMALS.items():
        for animal in animals:
            if animal["name"].lower() == name:
                return animal
    return None


@mcp.tool()
def get_animals_in_enclosure(enclosure: str) -> List[Dict]:
    enclosure = enclosure.lower()
    matches = []
    for animals in ZOO_ANIMALS.values():
        for animal in animals:
            if enclosure in animal["enclosure"].lower():
                matches.append(animal)
    return matches


@mcp.tool()
def list_all_animals() -> Dict[str, List[Dict]]:
    return ZOO_ANIMALS


@mcp.tool()
def get_zoo_map() -> Dict[str, str]:
    enclosures = {}
    for animals in ZOO_ANIMALS.values():
        for animal in animals:
            enclosure = animal["enclosure"]
            if enclosure not in enclosures:
                enclosures[enclosure] = f"Home to {animal['species']}"
    return enclosures


if __name__ == "__main__":
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )
