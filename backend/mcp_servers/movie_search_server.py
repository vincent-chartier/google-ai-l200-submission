"""MCP Server for Movie Discovery and Internet Search.

Provides MCP tools to search currently showing cinema films,
fetch detailed metadata, and locate theater showtimes.
"""

from mcp.server.fastmcp import FastMCP
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_movie_server")

# Initialize FastMCP Server
mcp = FastMCP("movie-search-server")

# Curated database of current and classic movies for simulation & grounding
MOVIES_DATABASE = [
    {
        "id": "dune-2",
        "title": "Dune: Part Two",
        "genres": ["Sci-Fi", "Adventure", "Action"],
        "year": 2024,
        "runtime": "166 min",
        "director": "Denis Villeneuve",
        "cast": ["Timothée Chalamet", "Zendaya", "Rebecca Ferguson", "Javier Bardem"],
        "imdb_rating": 8.6,
        "rotten_tomatoes": "93%",
        "synopsis": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the universe.",
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500",
        "in_theaters": True,
        "similarity_tags": ["Interstellar", "Blade Runner 2049", "Arrival", "Star Wars"]
    },
    {
        "id": "oppenheimer",
        "title": "Oppenheimer",
        "genres": ["Biography", "Drama", "History"],
        "year": 2023,
        "runtime": "180 min",
        "director": "Christopher Nolan",
        "cast": ["Cillian Murphy", "Emily Blunt", "Matt Damon", "Robert Downey Jr."],
        "imdb_rating": 8.9,
        "rotten_tomatoes": "93%",
        "synopsis": "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.",
        "poster_url": "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500",
        "in_theaters": False,
        "similarity_tags": ["The Imitation Game", "Interstellar", "Dunkirk"]
    },
    {
        "id": "interstellar",
        "title": "Interstellar",
        "genres": ["Sci-Fi", "Adventure", "Drama"],
        "year": 2014,
        "runtime": "169 min",
        "director": "Christopher Nolan",
        "cast": ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain"],
        "imdb_rating": 8.7,
        "rotten_tomatoes": "73%",
        "synopsis": "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, to find a new planet for humans.",
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500",
        "in_theaters": True, # Re-release special screening
        "similarity_tags": ["Arrival", "2001: A Space Odyssey", "Contact", "Dune: Part Two"]
    },
    {
        "id": "alien-romulus",
        "title": "Alien: Romulus",
        "genres": ["Sci-Fi", "Horror"],
        "year": 2024,
        "runtime": "119 min",
        "director": "Fede Álvarez",
        "cast": ["Cailee Spaeny", "David Jonsson", "Archie Renaux"],
        "imdb_rating": 7.3,
        "rotten_tomatoes": "80%",
        "synopsis": "While scavenging the deep ends of a derelict space station, a group of young space colonizers come face to face with the most terrifying life form in the universe.",
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500",
        "in_theaters": True,
        "similarity_tags": ["Alien", "Prometheus", "The Thing"]
    },
    {
        "id": "inside-out-2",
        "title": "Inside Out 2",
        "genres": ["Animation", "Adventure", "Comedy"],
        "year": 2024,
        "runtime": "96 min",
        "director": "Kelsey Mann",
        "cast": ["Amy Poehler", "Maya Hawke", "Kensington Tallman"],
        "imdb_rating": 7.7,
        "rotten_tomatoes": "91%",
        "synopsis": "Joy, Sadness, Anger, Fear and Disgust have been running a successful operation by all accounts. However, when Anxiety, Envy, Ennui and Embarrassment show up, headquarters undergoes a sudden demolition.",
        "poster_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500",
        "in_theaters": True,
        "similarity_tags": ["Inside Out", "Soul", "Coco"]
    },
    {
        "id": "gladiator-2",
        "title": "Gladiator II",
        "genres": ["Action", "Adventure", "Drama"],
        "year": 2024,
        "runtime": "148 min",
        "director": "Ridley Scott",
        "cast": ["Paul Mescal", "Pedro Pascal", "Denzel Washington"],
        "imdb_rating": 7.8,
        "rotten_tomatoes": "85%",
        "synopsis": "Years after witnessing the death of the revered hero Maximus at the hands of his uncle, Lucius must enter the Colosseum after his home is conquered by the tyrannical Emperors.",
        "poster_url": "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=500",
        "in_theaters": True,
        "similarity_tags": ["Gladiator", "Kingdom of Heaven", "Troy"]
    }
]

THEATERS_DATABASE = [
    {
        "theater_id": "metro-imax",
        "name": "Metropolis Cinema IMAX",
        "address": "450 7th Ave, Downtown",
        "screens": [
            {
                "screen_id": "SCR-1-IMAX",
                "screen_name": "IMAX Laser Hall",
                "format": "IMAX 70mm / 4K Laser",
                "sound": "12-Channel IMAX Audio",
                "rows": ["A", "B", "C", "D", "E", "F", "G", "H"],
                "seats_per_row": 8,
                "base_price": 19.50
            },
            {
                "screen_id": "SCR-2-DOLBY",
                "screen_name": "Dolby Cinema Suite",
                "format": "Dolby Vision + Atmos",
                "sound": "Dolby Atmos 64-channel",
                "rows": ["A", "B", "C", "D", "E", "F"],
                "seats_per_row": 8,
                "base_price": 17.00
            }
        ],
        "showtimes": {
            "Dune: Part Two": [
                {"showtime_id": "SH-DUNE-1630", "time": "16:30", "screen": "SCR-1-IMAX", "format": "IMAX Laser", "price": 19.50},
                {"showtime_id": "SH-DUNE-1930", "time": "19:30", "screen": "SCR-1-IMAX", "format": "IMAX Laser", "price": 19.50},
                {"showtime_id": "SH-DUNE-2215", "time": "22:15", "screen": "SCR-2-DOLBY", "format": "Dolby Cinema", "price": 17.00}
            ],
            "Interstellar": [
                {"showtime_id": "SH-INT-1800", "time": "18:00", "screen": "SCR-1-IMAX", "format": "IMAX 70mm Special", "price": 22.00},
                {"showtime_id": "SH-INT-2130", "time": "21:30", "screen": "SCR-1-IMAX", "format": "IMAX 70mm Special", "price": 22.00}
            ],
            "Alien: Romulus": [
                {"showtime_id": "SH-ALIEN-1745", "time": "17:45", "screen": "SCR-2-DOLBY", "format": "Dolby Cinema", "price": 17.00},
                {"showtime_id": "SH-ALIEN-2030", "time": "20:30", "screen": "SCR-2-DOLBY", "format": "Dolby Cinema", "price": 17.00}
            ],
            "Inside Out 2": [
                {"showtime_id": "SH-IO2-1400", "time": "14:00", "screen": "SCR-2-DOLBY", "format": "Standard Digital", "price": 14.50},
                {"showtime_id": "SH-IO2-1615", "time": "16:15", "screen": "SCR-2-DOLBY", "format": "Standard Digital", "price": 14.50}
            ],
            "Gladiator II": [
                {"showtime_id": "SH-GLAD-1900", "time": "19:00", "screen": "SCR-1-IMAX", "format": "IMAX Laser", "price": 19.50},
                {"showtime_id": "SH-GLAD-2200", "time": "22:00", "screen": "SCR-1-IMAX", "format": "IMAX Laser", "price": 19.50}
            ]
        }
    }
]


@mcp.tool()
def search_internet_movies(query: str = "", genre: str = "", in_theaters_only: bool = True) -> str:
    """Search for movies playing in theaters or available based on query or genre.
    
    Args:
        query: Search keywords, director names, actor names, or title fragments.
        genre: Target genre (e.g., 'Sci-Fi', 'Action', 'Drama', 'Horror', 'Animation').
        in_theaters_only: If true, only returns movies currently screening in cinemas.
        
    Returns:
        JSON string listing matching movies with metadata and ratings.
    """
    results = []
    q = query.lower().strip() if query else ""
    g = genre.lower().strip() if genre else ""

    for m in MOVIES_DATABASE:
        if in_theaters_only and not m.get("in_theaters", False):
            continue
            
        matches_q = True
        if q:
            matches_q = (
                q in m["title"].lower()
                or q in m["director"].lower()
                or any(q in actor.lower() for actor in m["cast"])
                or any(q in tag.lower() for tag in m.get("similarity_tags", []))
                or q in m["synopsis"].lower()
            )
            
        matches_g = True
        if g:
            matches_g = any(g in genre_item.lower() for genre_item in m["genres"])
            
        if matches_q and matches_g:
            results.append(m)
            
    return json.dumps(results, indent=2)


@mcp.tool()
def get_movie_details(title: str) -> str:
    """Fetch complete profile and details for a specific movie title.
    
    Args:
        title: Exact or partial title of the movie.
        
    Returns:
        JSON string with synopsis, cast, ratings, runtime, and poster.
    """
    t = title.lower().strip()
    for m in MOVIES_DATABASE:
        if t in m["title"].lower():
            return json.dumps(m, indent=2)
    return json.dumps({"error": f"Movie '{title}' not found in cinema catalog."})


@mcp.tool()
def get_theater_showtimes(movie_title: str, theater_name: str = "Metropolis Cinema IMAX") -> str:
    """Get active screening showtimes, formats, and pricing for a movie at a cinema.
    
    Args:
        movie_title: Name of the movie.
        theater_name: Name of the cinema venue.
        
    Returns:
        JSON string containing screening schedule, formats, and ticket prices.
    """
    t_name = theater_name.lower().strip()
    m_title = movie_title.lower().strip()
    
    for theater in THEATERS_DATABASE:
        if not t_name or t_name in theater["name"].lower():
            for film_key, showtimes in theater["showtimes"].items():
                if m_title in film_key.lower():
                    return json.dumps({
                        "theater": theater["name"],
                        "address": theater["address"],
                        "movie": film_key,
                        "showtimes": showtimes
                    }, indent=2)
                    
    return json.dumps({"error": f"No showtimes found for '{movie_title}' at '{theater_name}'."})


if __name__ == "__main__":
    mcp.run()
