# wilhelm.ai

An AI-powered radiology education tool that finds and summarizes authoritative Radiopaedia content to answer radiology-related questions. Built with FastHTML, DSPy, and modern LLM technology.

## Overview

wilhelm.ai combines large language models with radiological information from [Radiopaedia.org](https://radiopaedia.org) to provide fast, transparent, and educational answers to radiology questions. The application features intelligent search, content retrieval, and streaming answer generation with source verification.

## Features

- **Intelligent Search**: Uses DSPy to extract relevant medical topics from user queries
- **Content Retrieval**: Automatically finds and caches relevant Radiopaedia articles
- **Streaming Responses**: Real-time answer generation with visual feedback
- **Source Transparency**: Direct links to original Radiopaedia content for verification
- **Caching**: SQLite-based caching for improved performance
- **Modern UI**: Clean, responsive interface built with FastHTML and Tailwind CSS

## Architecture

The application consists of several key components:

- **Frontend** (`main.py`): FastHTML-based web interface with SSE streaming
- **Backend Logic** (`lib.py`): DSPy modules for search, retrieval, and answer generation
- **Database**: SQLite caching for search results and article content
- **Models**: Uses configurable LLM backends via DSPy

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd radiopaedia_idea
```

2. Install dependencies:
```bash
uv install
```

3. Create environment file:
```bash
cp .example.env .env
# Edit .env with your API keys and configuration
```

4. Initialize the database:
```bash
mkdir -p data
```

## Usage

### Running the Application

Start the development server:
```bash
uv run python main.py
```

The application will be available at `http://localhost:5001`.

### Example Queries

- "How do I differentiate between type 1 and type 2 endoleaks on CTA?"
- "What critical shoulder angle is normal?"
- "How can I differentiate hepatic adenoma from FNH?"
- "How do I classify hemorrhagic transformation of ischemic stroke?"

### Environment Variables

Configure the following in your `.env` file:

- `ANTHROPIC_API_KEY`: For Claude models
- `OPENAI_API_KEY`: For OpenAI models
- `GROQ_API_KEY`: For Groq models
- `DEVELOPMENT`: Set to `1` for development mode

## Project Structure

```
radiopaedia_idea/
├── main.py              # FastHTML web application
├── lib.py               # Core logic and DSPy modules
├── test_lib.py          # Unit tests
├── pyproject.toml       # Project configuration
├── requirements.txt     # Python dependencies
├── data/                # SQLite databases and cached data
├── models/              # Trained DSPy model files
├── assets/              # Static assets (SVG icons)
└── notes/               # Development notes
```

## Development

### Running Tests

```bash
uv run pytest test_lib.py
```

### Code Quality

The project uses Ruff for linting:
```bash
uv run ruff check .
```

### Model Training

DSPy models can be optimized and saved using the notebooks in the `notebooks/` directory. Trained models are stored in the `models/` directory.

## Important Disclaimers

⚠️ **This tool is NOT intended for clinical use** and should only be used for **demonstration, research, and educational purposes**.

⚠️ **Do NOT enter any patient data or sensitive information** into this application.

All medical content is provided under the [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 License](https://creativecommons.org/licenses/by-nc-sa/3.0/) from Radiopaedia.org.

## Contributing

This is a research and educational project. Contributions should focus on:

- Improving search accuracy and relevance
- Enhancing the user interface and experience
- Adding new evaluation metrics and datasets
- Documentation and code quality improvements

## License

This project uses content from Radiopaedia.org under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 License.

## Acknowledgments

- [Radiopaedia.org](https://radiopaedia.org) for providing the medical content
- [DSPy](https://github.com/stanfordnlp/dspy) for the prompt programming framework
- [FastHTML](https://github.com/AnswerDotAI/fasthtml) for the web framework
- [RadioRag](https://pubs.rsna.org/doi/10.1148/ryai.240476) - A paper describing and evaluating a system very similar to this
