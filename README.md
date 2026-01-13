# TradeOpenBB - AI-Powered Trading Platform

A modern, full-stack trading platform with AI-powered strategy generation, portfolio management, and real-time market data.

## 🚀 Features

- **Portfolio Management**: Create and manage multiple investment portfolios
- **AI Strategy Generation**: Generate trading strategies using AI (Gemini, OpenAI, Claude)
- **Real-time Market Data**: Get live stock quotes and market information
- **Backtesting**: Test strategies against historical data
- **Order Management**: Place and track trading orders
- **Position Tracking**: Monitor your holdings and performance

## 📁 Project Structure

```
TradeOpenBB/
├── render.yaml              # Render deployment configuration
├── .gitignore
├── README.md
├── docker-compose.yml       # Local development with Docker
│
├── backend/                 # FastAPI backend
│   ├── Dockerfile
│   ├── main.py             # API endpoints
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # Database connection
│   ├── requirements.txt    # Python dependencies
│   ├── ai_providers/       # AI service providers
│   └── tests/              # Backend tests
│
├── components/             # React components
│   ├── Dashboard.tsx
│   ├── TradePanel.tsx
│   ├── StrategyLab.tsx
│   └── ...
│
├── services/               # Frontend services
│   ├── apiClient.ts
│   ├── tradingService.ts
│   └── ...
│
├── docs/                   # Documentation
└── scripts/               # Utility scripts
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite/PostgreSQL** - Database
- **Pydantic** - Data validation
- **OpenBB** - Market data integration

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization

### AI Integration
- **Google Gemini** - AI strategy generation
- **OpenAI** - Alternative AI provider
- **Anthropic Claude** - Alternative AI provider

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, SQLite works for development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/indamices/TradeOpenBB.git
   cd TradeOpenBB
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Frontend Setup**
   ```bash
   npm install
   
   # Create .env.local file
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
   ```

4. **Start Services**
   ```bash
   # Terminal 1: Backend
   cd backend
   uvicorn main:app --reload
   
   # Terminal 2: Frontend
   npm run dev
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Development

```bash
docker-compose up -d
```

## 📦 Deployment

### Render (Recommended)

This project is configured for easy deployment on Render.

1. **Push to GitHub** (already done)
   - Repository: `https://github.com/indamices/TradeOpenBB`

2. **Deploy on Render**
   - Visit https://render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml` and deploy

3. **Configure Environment Variables**
   - `ENCRYPTION_KEY` - Auto-generated
   - `GEMINI_API_KEY` - Your Gemini API key (optional)
   - `API_KEY` - External API key (optional)

See [docs/RENDER_QUICK_START.md](docs/RENDER_QUICK_START.md) for detailed deployment instructions.

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md)
- [Render Quick Start](docs/RENDER_QUICK_START.md)
- [Render Full Guide](docs/RENDER_DEPLOYMENT_GUIDE.md)
- [Setup Instructions](docs/SETUP.md)
- [Docker Setup](docs/DOCKER_SETUP.md)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Run specific test file
pytest tests/test_api_portfolio.py
```

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=sqlite:///./data/smartquant.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/smartquant_db

ENCRYPTION_KEY=your-32-character-encryption-key
GEMINI_API_KEY=your-gemini-api-key
API_KEY=your-api-key
```

### Frontend Environment Variables

Create `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🔗 Links

- **GitHub Repository**: https://github.com/indamices/TradeOpenBB
- **Render Dashboard**: https://dashboard.render.com
- **API Documentation**: Available at `/docs` endpoint when backend is running

## 💡 Support

For issues and questions:
- Check the [documentation](docs/)
- Open an issue on GitHub
- Review deployment guides in `docs/` directory

---

**Built with ❤️ using FastAPI, React, and AI**
