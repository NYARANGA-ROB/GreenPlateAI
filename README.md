# GreenPlateAI - University Food Waste Reduction Platform

## Overview

GreenPlateAI is an AI-powered platform designed to help universities reduce food waste through intelligent forecasting, real-time monitoring, and actionable recommendations. The application uses machine learning algorithms to predict food consumption patterns, optimize meal planning, and provide insights for sustainable dining operations.

## Features

- **🤖 AI-Powered Forecasting**: Predict food demand using advanced machine learning models
- **📊 Real-time Dashboards**: Interactive visualizations of food waste metrics and trends
- **🎯 Smart Recommendations**: Data-driven insights to reduce waste and optimize operations
- **📈 Analytics & Reports**: Comprehensive reporting for sustainability tracking
- **🔐 Secure Authentication**: Role-based access control for different user types
- **📱 Responsive Design**: Mobile-friendly interface built with Streamlit

## Technology Stack

- **Frontend**: Streamlit 1.29.0
- **Backend**: Python 3.9+
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: Scikit-learn, XGBoost, LightGBM
- **Visualization**: Plotly, Seaborn, Matplotlib
- **Data Processing**: Pandas, NumPy
- **Security**: bcrypt, cryptography, passlib

## Project Structure

```
GreenPlateAI/
│
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # Project documentation
│
├── database/             # Database configuration and migrations
│   ├── __init__.py
│   ├── connection.py     # Database connection management
│   └── migrations/       # Alembic migration files
│
├── models/               # SQLAlchemy data models
│   ├── __init__.py
│   ├── base.py          # Base model class
│   ├── user.py          # User authentication models
│   ├── food_item.py     # Food item and inventory models
│   ├── waste_record.py  # Food waste tracking models
│   └── prediction.py    # ML prediction models
│
├── pages/                # Streamlit page modules
│   ├── __init__.py
│   ├── dashboard.py     # Main dashboard page
│   ├── forecasting.py   # Food demand forecasting
│   ├── recommendations.py # AI recommendations
│   ├── reports.py       # Data export and reports
│   └── settings.py      # Application settings
│
├── utils/                # Utility functions and helpers
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── data_loader.py   # Data loading utilities
│   ├── validators.py    # Input validation
│   └── helpers.py       # General helper functions
│
├── auth/                 # Authentication and authorization
│   ├── __init__.py
│   ├── authenticator.py  # User authentication logic
│   ├── decorators.py     # Authentication decorators
│   └── permissions.py    # Role-based permissions
│
├── forecasting/          # Machine learning forecasting
│   ├── __init__.py
│   ├── models.py        # ML model implementations
│   ├── features.py      # Feature engineering
│   ├── training.py      # Model training pipeline
│   └── prediction.py    # Prediction interface
│
├── dashboards/           # Dashboard components
│   ├── __init__.py
│   ├── charts.py        # Chart creation utilities
│   ├── metrics.py       # KPI calculations
│   └── layouts.py       # Dashboard layout components
│
├── recommendations/      # Recommendation engine
│   ├── __init__.py
│   ├── engine.py        # Core recommendation logic
│   ├── rules.py         # Business rule engine
│   └── insights.py      # Insight generation
│
├── reports/              # Reporting and data export
│   ├── __init__.py
│   ├── generators.py    # Report generation
│   ├── exporters.py     # Data export utilities
│   └── templates.py     # Report templates
│
├── assets/               # Static assets
│   ├── images/          # Images and icons
│   ├── css/             # Custom CSS styles
│   └── js/              # JavaScript files
│
└── data/                 # Data storage
    ├── raw/             # Raw data files
    ├── processed/       # Processed data
    └── models/          # Saved ML models
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GreenPlateAI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -c "from database.connection import init_db; init_db()"
   ```

## Usage

### Development Mode

```bash
streamlit run app.py
```

### Production Mode

```bash
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

Or using Gunicorn:

```bash
gunicorn -w 4 -k streamlit.server.app.ServerRunner:run app:app
```

## Configuration

The application uses environment variables for configuration. Key settings include:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Application secret key for security
- `AUTH_ENABLED`: Enable/disable authentication
- `MODEL_RETRAINING_DAYS`: Frequency of model retraining
- `FORECASTING_DAYS_AHEAD`: Number of days to forecast

See `.env.example` for all available configuration options.

## API Reference

### Authentication Endpoints

- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/register` - User registration

### Data Endpoints

- `GET /api/waste/records` - Get waste records
- `POST /api/waste/records` - Create waste record
- `GET /api/forecasting/predict` - Get food demand predictions

## Machine Learning Models

The application includes several ML models:

1. **Demand Forecasting**: Predicts food demand for menu items
2. **Waste Prediction**: Estimates potential food waste
3. **Optimization**: Recommends optimal preparation quantities

Models are automatically retrained based on the `MODEL_RETRAINING_DAYS` setting.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

Run the test suite:

```bash
pytest tests/
```

For coverage:

```bash
pytest --cov=. tests/
```

## Deployment

### Docker Deployment

```bash
docker build -t greenplateai .
docker run -p 8501:8501 greenplateai
```

### Cloud Deployment

The application can be deployed to:
- Heroku
- AWS (Elastic Beanstalk, ECS)
- Google Cloud Platform
- Azure

See the deployment documentation for specific instructions.

## Security

- Password hashing with bcrypt
- JWT token authentication
- SQL injection prevention with SQLAlchemy
- Input validation and sanitization
- HTTPS enforcement in production

## Performance

- Database connection pooling
- Model caching for faster predictions
- Lazy loading of dashboard components
- Optimized database queries

## Monitoring

- Application logging with structured logs
- Performance metrics collection
- Error tracking with Sentry (optional)
- Database query monitoring

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@greenplateai.com
- Documentation: https://docs.greenplateai.com

## Acknowledgments

- University dining services partners
- Sustainability research teams
- Open source contributors
- Machine learning community

## Roadmap

- [ ] Mobile app development
- [ ] Integration with university systems
- [ ] Advanced ML models
- [ ] Multi-campus support
- [ ] Real-time IoT sensor integration
- [ ] Blockchain for waste tracking
