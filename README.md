# Wizard Agent 🤖✨

A powerful AI-powered WhatsApp bot that processes messages, creates stickers, and downloads media from various platforms with a touch of humor and personality.

## 🌟 Features

- **Smart Message Processing**
  - Multi-language support
  - Context-aware responses
  - Humorous and emoji-rich interactions
  - WhatsApp-style formatting

- **Media Download Support**
  - Facebook videos and posts
  - Instagram reels and posts
  - TikTok videos
  - YouTube videos
  - Twitter posts

- **Sticker Creation**
  - Convert images to WhatsApp stickers
  - Custom sticker packs
  - Easy-to-use interface

- **Advanced Features**
  - PostgreSQL database for conversation history
  - Context summarization
  - Language detection
  - Async processing
  - Docker support

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- OpenRouter API key
- Docker (optional)

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions

# Server Configuration
PORT=8000
HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database
```

### Docker Deployment

1. Build the image:
```bash
docker build -t Wizard-Agent .
```

2. Run the container:
```bash
docker run -d \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key \
  -e OPENROUTER_API_URL=your_url \
  -e DATABASE_URL=your_postgres_url \
  Wizard-Agent
```

## 🏗️ Architecture

### Components

- **FastAPI Backend**: Handles webhook requests and message processing
- **OpenRouter AI**: Powers the conversation and language detection
- **PostgreSQL**: Stores conversation history and user context
- **Docker**: Containerized deployment
- **GitHub Actions**: Automated builds and deployments

### Database Schema


## 🔧 Configuration

### API Endpoints

- `POST /webhook`: Main webhook endpoint for WhatsApp messages
  - Accepts JSON payload with message and user information
  - Returns AI-generated response

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| OPENROUTER_API_KEY | OpenRouter API key | Yes | - |
| OPENROUTER_API_URL | OpenRouter API endpoint | Yes | - |
| PORT | Server port | No | 8000 |
| HOST | Server host | No | 0.0.0.0 |
| DATABASE_URL | PostgreSQL connection string | Yes | - |

## 🛠️ Development

### Project Structure

```
Wizard-Agent/
├── .github/
│   └── workflows/
│       └── docker-build.yml
├── main.py
├── database.py
├── database_config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📦 Deployment

### Docker

The project includes a GitHub Actions workflow for automated Docker builds:

- Builds on push to main branch
- Supports multi-platform builds (amd64, arm64)
- Implements layer caching for faster builds
- Pushes to GitHub Container Registry

### Manual Deployment

1. Set up PostgreSQL database
2. Configure environment variables
3. Build and run Docker container
4. Set up webhook URL in WhatsApp Business API

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Created by [Mahmoud Nasr](https://github.com/gitnasr)

## 🙏 Acknowledgments

- OpenRouter for AI capabilities
- FastAPI for the web framework
- PostgreSQL for database
- Docker for containerization 