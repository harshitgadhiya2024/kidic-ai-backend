# Kidic AI - Authentication System

A production-ready FastAPI authentication system with email-based OTP verification, JWT tokens, MongoDB, and AWS integrations.

## Features

✨ **Email OTP Authentication** - Secure login/signup with time-limited OTP codes  
🔐 **JWT Tokens** - Access and refresh token management  
📧 **AWS SES** - Professional email delivery  
☁️ **AWS S3** - File upload and storage  
🗄️ **MongoDB** - Scalable NoSQL database  
🏗️ **Clean Architecture** - Well-organized, production-ready code structure  

## Tech Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: MongoDB (Motor - async driver)
- **Authentication**: JWT (PyJWT library)
- **Email**: AWS SES (boto3)
- **Storage**: AWS S3 (boto3)

## Project Structure

```
kidic-ai/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config/              # Configuration management
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic validation schemas
│   ├── api/v1/              # API v1 endpoints
│   ├── core/                # Security & dependencies
│   ├── services/            # Business logic services
│   ├── database/            # MongoDB connection
│   └── utils/               # Utility functions
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or Atlas)
- AWS Account with SES and S3 configured
- pip (Python package manager)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd "/Users/harshitgadhiya/PycharmProjects/kidic ai"
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and configure:

- **MongoDB URI**: Your MongoDB connection string
- **JWT Secret**: A strong secret key for JWT tokens
- **AWS Credentials**: Your AWS access key, secret key, and region
- **AWS SES**: Your verified sender email
- **AWS S3**: Your S3 bucket name

### 5. Set up AWS SES

1. Verify your sender email in AWS SES console
2. If in SES sandbox, verify recipient emails too
3. Request production access for unrestricted sending

### 6. Set up AWS S3

1. Create an S3 bucket
2. Configure bucket permissions for public read access
3. Update bucket name in `.env`

## Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

#### Send OTP
```http
POST /api/v1/auth/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Verify OTP & Login/Register
```http
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

Returns JWT tokens and user information. Creates new user if doesn't exist.

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

## User Model

New users are automatically created with:

```json
{
  "username": "user_email",
  "email": "user@example.com",
  "profile_picture": null,
  "credits": 10,
  "is_active": true,
  "created_at": "2024-01-19T10:00:00",
  "updated_at": "2024-01-19T10:00:00"
}
```

## Authentication Flow

1. **User enters email** → System sends OTP via AWS SES
2. **OTP expires in 10 minutes** (configurable)
3. **User enters OTP** → System verifies code
4. **If valid**:
   - If user exists → Return user data + JWT tokens
   - If new user → Create user with default credits → Return user data + JWT tokens
5. **User is authenticated** → Can access protected endpoints

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB connection string | Yes |
| `MONGODB_DB_NAME` | Database name | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) | No |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `AWS_REGION` | AWS region | Yes |
| `AWS_SES_SENDER_EMAIL` | Verified SES sender email | Yes |
| `AWS_S3_BUCKET_NAME` | S3 bucket name | Yes |
| `OTP_EXPIRE_MINUTES` | OTP expiration time (default: 10) | No |
| `DEFAULT_USER_CREDITS` | Default credits for new users (default: 10) | No |

## Security Features

- ✅ JWT-based authentication
- ✅ OTP with time-based expiration
- ✅ One-time use OTP codes
- ✅ Secure password-less authentication
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ MongoDB indexes for performance
- ✅ Automatic OTP cleanup (TTL index)

## Development

### Add New Endpoints

1. Create endpoint file in `app/api/v1/endpoints/`
2. Add router to `app/api/v1/router.py`
3. Follow existing patterns for consistency

### Database Indexes

Indexes are automatically created on startup:
- Users: `email` (unique)
- OTPs: `email`, `expires_at`, TTL index

## Troubleshooting

### MongoDB Connection Issues
- Verify MongoDB is running
- Check connection URI format
- Ensure network access (for Atlas)

### AWS SES Email Not Sending
- Verify sender email in SES console
- Check SES sandbox restrictions
- Verify AWS credentials

### JWT Token Issues
- Ensure JWT_SECRET_KEY is set
- Check token expiration times
- Verify Authorization header format: `Bearer <token>`

## License

This project is private and proprietary.

## Support

For issues or questions, contact the development team.
