import requests

# server = "http://localhost:8000"
server = "http://10.12.246.125:8000"

def query(use_cases: dict):
    prompt = (
        f"You get a use cases of a code repository. Is the EU AI Act relevant for this project? Use cases: {use_cases}"
    )
    files = {
        "question": (None, prompt),
        "session_id": (None, "b3d0764f-a66f-461b-a8b8-d69b6d9c455a"),
        "model": (None, "openai_gpt_4o"),
        "mode": (None, "graph_vector_fulltext"),
        "document_names": (None, "[]"),
        "uri": (None, "neo4j://database:7687"),
        "database": (None, "neo4j"),
        "userName": (None, "neo4j"),
        "password": (None, "neo4j"),
    }

    url = f"{server}/chat_bot"

    headers = {
        "Accept": "application/json, text/plain, */*",
        # "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        # "Connection": "keep-alive",
        # "Origin": "http://localhost:8080",
        # "Referer": "http://localhost:8080/",
        # "Sec-Fetch-Dest": "empty",
        # "Sec-Fetch-Mode": "cors",
        # "Sec-Fetch-Site": "same-site",
    }

    return requests.post(url, headers=headers, files=files)
