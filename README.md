# WhatsAppWizard 🤖✨

WhatsAppWizard is an AI-powered WhatsApp bot that can process messages in multiple languages, create stickers, and download media from various social media platforms.

## Features 🌟

- Multi-language message processing
- AI-powered responses with humor and emojis
- Media download support for:
  - Facebook
  - Instagram
  - TikTok
  - YouTube
  - Twitter
- Sticker creation from images
- OpenRouter AI integration

## Prerequisites 📋

- Python 3.8+
- OpenRouter API key
- WhatsApp Business API access
- Docker (for containerized deployment)

## Installation 🚀

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whatsapp-wizard.git
cd whatsapp-wizard
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```
OPENROUTER_API_KEY=your_openrouter_api_key
```

### Docker Deployment

1. Build and run using Docker:
```bash
# Build the image
docker build -t whatsapp-wizard .

# Run the container
docker run -p 8000:8000 -e OPENROUTER_API_KEY=your_api_key whatsapp-wizard
```

2. Or use Docker Compose:
```bash
# Create .env file with your API key
echo "OPENROUTER_API_KEY=your_api_key" > .env

# Build and run
docker-compose up --build
```

## GitHub Actions Workflow 🔄

The repository includes a GitHub Actions workflow that automatically:
- Builds the Docker image on push to main branch
- Builds and tests on pull requests
- Pushes the image to GitHub Container Registry (ghcr.io)
- Uses Docker layer caching for faster builds
- Tags images based on:
  - Branch name
  - Pull request number
  - Semantic versioning
  - Git SHA

To use the workflow:
1. Enable GitHub Actions in your repository
2. Ensure your repository has access to GitHub Packages
3. Push to main branch or create a pull request

## Usage 💡

1. Start the server:
```bash
# Local development
python main.py

# Or using Docker
docker-compose up
```

2. The server will start on `http://localhost:8000`

3. Configure your WhatsApp Business API webhook to point to:
```
http://your-domain/webhook
```

## API Endpoints 🔌

- `POST /webhook`: Receives WhatsApp messages and processes them

## Response Format 📝

The bot responds with JSON in the following format:
```json
{
    "response": "AI-generated response with emojis 😊",
    "media": {
        "type": "video/image",
        "url": "media_url",
        "title": "media_title"
    }
}
```

## Docker Configuration 🐳

The project includes:
- `Dockerfile` for containerization
- `docker-compose.yml` for easy deployment
- `.dockerignore` for optimized builds
- GitHub Actions workflow for automated builds

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details. 