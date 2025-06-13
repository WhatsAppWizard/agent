<img width="128" src="https://github.com/user-attachments/assets/0e126a28-e0a3-46da-987c-34fc8bbd2567"/>

# Wizard Agent 

A conversational AI agent for WhatsApp, providing helpful support and explanations.

[![Docker Build Status](https://img.shields.io/github/actions/workflow/status/gitnasr/Wizard-Agent/docker-build.yml?branch=main&label=Docker%20Build)](https://github.com/gitnasr/Wizard-Agent/actions/workflows/docker-build.yml)
[![License](https://img.shields.io/github/license/gitnasr/Wizard-Agent)](https://github.com/gitnasr/Wizard-Agent/blob/main/LICENSE)


Wizard-Agent is designed to enhance WhatsApp interactions by providing users with AI-powered assistance. It focuses on explaining features, answering questions, and guiding users on how to utilize various services, without performing the actions themselves.

## Table of Contents
1. [Key Features ✨](#key-features-)
2. [Technology Stack 🛠️](#technology-stack-%EF%B8%8F)
3. [Getting Started 🚀](#getting-started-)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
    - [Running the Project](#running-the-project)
4. [Usage Examples 💡](#usage-examples-)
5. [Project Structure 📁](#project-structure-)
6. [Contributing 🤝](#contributing-)
7. [Testing 🧪](#testing-)
8. [Deployment 🚀](#deployment-)
9. [API Documentation 📚](#api-documentation-)
10. [Roadmap 🗺️](#roadmap)
11. [Support & Contact 💬](#support--contact-)
12. [License 📄](#license-)
13. [Acknowledgments 🙏](#acknowledgments-)

## Key Features ✨

- **Multi-Language Support:** Communicates with users in their preferred language, detected automatically.
- **Context-Aware Conversations:** Remembers previous conversations to provide more relevant and personalized responses.
- **Sticker Creation Guidance:** Explains how users can turn images into custom stickers within WhatsApp. (Note: The service only *explains* how, it does not perform the sticker creation itself.)
- **Media Download Support (Explanation):** Guides users on how to download content from various platforms like Facebook, Instagram, TikTok, YouTube, and Twitter. (Note: The service only *explains* how, it does not perform the downloads itself.)
- **Engaging and Friendly Personality:** Designed to be a helpful and supportive companion, providing clear and easy-to-understand guidance.


## Technology Stack 🛠️

- **Languages**:
  - Python
- **Frameworks**:
  - FastAPI
  - SQLAlchemy
- **Tools**:
  - Uvicorn
  - Docker
  - Alembic
- **Services**:
  - OpenRouter API
  - PostgreSQL

## Getting Started 🚀

Follow these steps to get Wizard-Agent up and running on your local machine or server.

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized deployment)
- An OpenRouter API key (required for AI response generation)
- PostgreSQL database instance

### Installation

1.  Clone the repository:

```bash
git clone https://github.com/gitnasr/Wizard-Agent.git
cd Wizard-Agent
```

2.  Create a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

3.  Install the required Python packages, make sure you are in the root directory of the project:

```bash
pip install -r requirements.txt
```

### Configuration

1.  Set up environment variables:

    -   Create a `.env` file in the project root directory, based on the `.env.example` provided (TODO: Add .env.example to the repo for clarity). Or you can set the env variables through your system/Hosting provider.
    -   Add the following variables, replacing the placeholders with your actual values:

```
OPENROUTER_API_KEY=<YOUR_OPENROUTER_API_KEY>
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_wizard # Or your own db URL
PORT=8000
HOST=0.0.0.0
```

2. Configure the database:  

Make sure the database you specified in the `DATABASE_URL` variable is available and running.  
You will also need to run the database initialization:
```python
# Run this code snippet in your python interpreter to initialize the database
from database import ConversationDB
import asyncio

async def initialize_database():
    db = ConversationDB()
    await db.init_db()

asyncio.run(initialize_database())
```

### Running the Project

1.  Start the FastAPI application using Uvicorn:

```bash
python main.py
```

Alternatively, you can run using Uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2.  Access the API documentation at `http://localhost:8000/docs` (or the appropriate host and port if you've configured them differently).

## Usage Examples 💡

The Wizard-Agent is designed to be integrated with a WhatsApp messaging platform. Here are some example scenarios

1.  **Receiving a Message:**
    The `/webhook` endpoint receives incoming messages from WhatsApp. The expected JSON payload structure is:

```json
{
  "message": {
    "text": "Hello, how can I download tiktok videos?"
  },
  "user": {
    "id": "user123"
  }
}
```

2.  **Processing the Message:**
    The agent processes the message, detects the language (if not already provided), and generates a response using the OpenRouter API.

3.  **Sending a Response:**
    The agent provides an appropriate response back to the user via the WhatsApp platform. The response might look something like:

```json
{
  "response": "Hello! I am here to help. To download TikTok videos, ..."
}
```

## Project Structure 📁

```
Wizard-Agent/
├── .github/workflows/         # GitHub Actions workflows for CI/CD
├── .dockerignore              # Specifies intentionally untracked files that Git should ignore
├── Dockerfile                 # Docker configuration file
├── README.md                  # This file
├── database.py                # Database interaction logic (SQLAlchemy models, CRUD operations)
├── database_config.py            # Database configuration (SQLAlchemy setup)
├── docker-compose.yml         # Docker Compose file to run services
├── main.py                    # Main application file. Contains FastAPI endpoints and application logic
├── requirements.txt           # List of Python dependencies
```

## Contributing 🤝

Contributions are welcome! Please follow these guidelines:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and write tests.
4.  Submit a pull request.

To set up your development environment:

1.  Follow the [Installation](#installation) instructions.
2.  Install development dependencies (e.g., linters, formatters).  TODO: Add dev dependecies in a requirements-dev.txt .
3.  Configure your editor for linting and formatting.

If you find a bug or have a feature request, please open an issue on GitHub.


## Deployment 🚀

To deploy Wizard-Agent to production:

1.  Build the Docker image:

```bash
docker build -t wizard-agent .
```

2.  Push the image to a container registry (e.g., Docker Hub):

```bash
docker tag wizard-agent:latest <your_dockerhub_username>/wizard-agent:latest
docker push <your_dockerhub_username>/wizard-agent:latest
```

3.  Deploy the container to your preferred hosting platform (e.g., AWS, Google Cloud, Azure).

4.  Configure environment variables in your hosting environment.

5.  Ensure that the application can access the PostgreSQL database.

## API Documentation 📚

Detailed API documentation is available at:

`http://localhost:8000/docs`

Key endpoints:

-   `/webhook` (POST): Handles incoming messages from the WhatsApp platform.

## Roadmap 🗺️

-   [ ] Implement context summarization to handle long conversations more effectively.
-   [ ] Add more robust error handling and logging.
-   [ ] Develop comprehensive unit and integration tests.
-   [ ] Explore more advanced AI models for improved response quality.

## Support & Contact 💬

If you have questions or need help, please:

-   Open an issue on GitHub: [https://github.com/gitnasr/Wizard-Agent/issues](https://github.com/gitnasr/Wizard-Agent/issues)
-   Contact me through my GitHub profile: [https://github.com/gitnasr](https://github.com/gitnasr)

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

-   The Wizard-Agent uses the [OpenRouter](https://openrouter.ai/) API to generate AI responses, making it possible to easly use multiple LLMs.
-   Thanks to the FastAPI and SQLAlchemy communities for providing excellent tools for building web applications and interacting with databases.
