# EU AI Act Compliance Checker

This application analyzes GitHub repositories to assess their compliance with the European Union's AI Act. It provides a technical description of the repository's functionalities and identifies the relevant sections of the EU AI Act that may apply.

## Features

- Clone and analyze GitHub repositories
- Extract technical features and capabilities from code
- Load and process the EU AI Act
- Compare repository features against AI Act requirements
- Generate compliance reports with relevant sections highlighted

## Architecture

The application uses:
- LangGraph for agent-based workflows
- LangChain for LLM integration
- Streamlit for the user interface
- FAISS for vector storage and similarity search

## Setup

1. Clone this repository
2. Install dependencies with `pip install -e .`
3. Create a `.env` file with your API keys
4. Run the application with `streamlit run app/ui/main.py`

## Environment Variables

Create a `.env` file with the following:
```
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token  # Optional for public repositories
```

Note: The GitHub token is optional if you're only analyzing public repositories.

## License

MIT
