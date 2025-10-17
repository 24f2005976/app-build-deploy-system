# App Build Deploy System

A comprehensive system for students to build, deploy, and update applications automatically, with instructor evaluation capabilities.

## Overview

This system implements the complete workflow described in the project requirements:

1. **Build Phase**: Students receive JSON requests, generate apps using LLM assistance, create GitHub repos, and deploy to GitHub Pages
2. **Evaluate Phase**: Instructors run automated checks (static, dynamic, LLM-based) and store results
3. **Revise Phase**: Students receive second requests to modify their apps and redeploy

## Project Structure

```
app-build-deploy-system/
├── student_api/           # Student-facing API endpoint
│   └── app.py            # Main Flask application for students
├── evaluation_system/     # Instructor evaluation tools
│   ├── evaluation_api.py # API for receiving repo notifications
│   ├── round1.py         # Generate and send round 1 tasks
│   ├── round2.py         # Generate and send round 2 tasks
│   └── evaluate.py       # Repository evaluation script
├── database/             # Database management
│   └── database.py       # SQLite database operations
├── templates/            # Sample files and templates
│   └── submissions.csv   # Sample submissions format
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.template        # Environment variables template
└── README.md           # This file
```

## Features

### Student API (`student_api/app.py`)
- ✅ Accepts JSON POST requests with task briefs
- ✅ Verifies student secrets
- ✅ LLM-assisted app generation (OpenAI + fallback)
- ✅ GitHub repository creation and management
- ✅ Automatic GitHub Pages deployment
- ✅ MIT license and professional README generation
- ✅ Evaluation API notification with exponential backoff
- ✅ Support for both round 1 and round 2 requests
- ✅ Attachment processing (data URIs)

### Evaluation System
- ✅ **Database Management**: SQLite with tables for tasks, repos, and results
- ✅ **Evaluation API**: Receives repo submission notifications
- ✅ **Round 1 Generator**: Creates and sends initial tasks to students
- ✅ **Round 2 Generator**: Creates enhancement tasks based on round 1 completions
- ✅ **Repository Evaluator**: Automated checks including:
  - MIT license verification
  - README.md quality assessment (LLM-based)
  - Code quality evaluation (LLM-based)
  - GitHub Pages accessibility
  - Dynamic functionality testing (Playwright)

### Task Templates
Pre-defined task types with round 1 and round 2 variations:
- **Captcha Solver**: Image processing and text extraction
- **Weather Dashboard**: API integration and responsive design
- **Todo Manager**: CRUD operations and local storage

## Setup Instructions

### 1. Environment Setup

1. **Clone and Navigate**:
   ```bash
   cd c:\Users\pravijap\OneDrive - Capgemini\Desktop\IITM\app-build-deploy-system
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright Browsers** (for dynamic testing):
   ```bash
   playwright install
   ```

### 2. Configuration

1. **Copy Environment Template**:
   ```bash
   copy .env.template .env
   ```

2. **Edit `.env` file** with your credentials:
   ```env
   GITHUB_TOKEN=ghp_your_github_token_here
   OPENAI_API_KEY=sk-your_openai_key_here
   STUDENT_SECRET=your_secret_from_form
   ```

3. **Get GitHub Token**:
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Create token with `repo`, `admin:org`, `admin:repo_hook` permissions

4. **Get OpenAI API Key** (optional):
   - Sign up at OpenAI and get API key
   - System will use fallback generator if not provided

### 3. Database Initialization

```bash
python database/database.py
```

## Usage

### For Students

1. **Start Student API**:
   ```bash
   python student_api/app.py
   ```
   Server runs on `http://localhost:5000`

2. **API Endpoints**:
   - `POST /api/build` - Main endpoint for task requests
   - `GET /health` - Health check

3. **Example Request**:
   ```bash
   curl -X POST http://localhost:5000/api/build \
     -H "Content-Type: application/json" \
     -d '{
       "email": "student@example.com",
       "secret": "your_secret",
       "task": "captcha-solver-abc123",
       "round": 1,
       "nonce": "unique-nonce",
       "brief": "Create a captcha solver...",
       "checks": ["Repo has MIT license", "..."],
       "evaluation_url": "http://localhost:5001/api/notify",
       "attachments": []
     }'
   ```

### For Instructors

1. **Start Evaluation API**:
   ```bash
   python evaluation_system/evaluation_api.py
   ```
   Server runs on `http://localhost:5001`

2. **Run Round 1 Tasks**:
   ```bash
   python evaluation_system/round1.py \
     --submissions templates/submissions.csv \
     --evaluation-url http://localhost:5001/api/notify
   ```

3. **Evaluate Repositories**:
   ```bash
   python evaluation_system/evaluate.py \
     --openai-key sk-your_key_here
   ```

4. **Run Round 2 Tasks**:
   ```bash
   python evaluation_system/round2.py \
     --evaluation-url http://localhost:5001/api/notify
   ```

## API Reference

### Student API

#### POST /api/build
Build and deploy an application.

**Request Body**:
```json
{
  "email": "string",
  "secret": "string", 
  "task": "string",
  "round": 1 | 2,
  "nonce": "string",
  "brief": "string",
  "checks": ["string"],
  "evaluation_url": "string",
  "attachments": [{"name": "string", "url": "data:..."}]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Application built and deployed successfully",
  "repo_url": "https://github.com/user/repo",
  "pages_url": "https://user.github.io/repo/",
  "commit_sha": "abc123",
  "pages_enabled": true,
  "evaluation_notified": true
}
```

### Evaluation API

#### POST /api/notify
Receive repository submission notifications.

#### GET /api/results?email=&task=
Get evaluation results.

#### GET /api/tasks?email=&round=
Get task records.

#### GET /api/repos?email=&round=
Get repository submissions.

## Database Schema

### Tables

1. **tasks**: Stores tasks sent to students
2. **repos**: Stores repository submissions  
3. **results**: Stores evaluation results
4. **submissions**: Stores student form submissions

### Key Fields

- **tasks**: email, task, round, nonce, brief, checks, evaluation_url, endpoint, statuscode
- **repos**: email, task, round, nonce, repo_url, commit_sha, pages_url
- **results**: email, task, round, check_name, score, reason, logs

## Security Features

- ✅ Secret verification for all requests
- ✅ Input validation and sanitization
- ✅ No secrets stored in git history
- ✅ Secure GitHub token handling
- ✅ Request timeout and rate limiting
- ✅ Error handling without exposing internals

## Evaluation Criteria

### Automated Checks

1. **Repository Checks**:
   - MIT license present
   - Repository created after task time
   - Public accessibility

2. **README Quality** (LLM-scored 0.0-1.0):
   - Professional presentation
   - Clear structure
   - Setup instructions
   - Usage examples
   - License information

3. **Code Quality** (LLM-scored 0.0-1.0):
   - Organization and structure
   - Comments and documentation
   - Error handling
   - Best practices
   - Functionality implementation

4. **GitHub Pages**:
   - Accessibility (HTTP 200)
   - Content presence
   - Task-specific functionality

5. **Dynamic Testing** (Playwright):
   - Page loads without errors
   - Interactive elements work
   - URL parameter handling
   - Task-specific features

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**:
   - Use authenticated requests
   - Implement delays between operations

2. **OpenAI API Errors**:
   - Check API key validity
   - Monitor usage limits
   - System falls back gracefully

3. **GitHub Pages Deployment**:
   - Pages may take 5-10 minutes to deploy
   - Check repository settings
   - Ensure `index.html` exists

4. **Database Locks**:
   - Close connections properly
   - Use transactions for multi-step operations

### Environment Variables

Ensure all required environment variables are set:
- `GITHUB_TOKEN` - Required for GitHub operations
- `STUDENT_SECRET` - Required for request verification
- `OPENAI_API_KEY` - Optional, fallback available

## Development

### Adding New Task Templates

1. Edit `evaluation_system/round1.py`
2. Add new template to `TaskTemplates.get_templates()`
3. Include both round 1 and round 2 variations
4. Update round 2 generation logic if needed

### Extending Evaluation Checks

1. Edit `evaluation_system/evaluate.py`
2. Add new check methods to `RepositoryEvaluator`
3. Update `evaluate_repository()` to include new checks
4. Ensure results are stored with appropriate scores

## Production Deployment

### Security Considerations

1. **Environment Variables**:
   - Use secure secret management
   - Rotate tokens regularly
   - Set strong Flask secret keys

2. **Database**:
   - Use PostgreSQL for production
   - Implement backup strategies
   - Set up monitoring

3. **API Security**:
   - Implement rate limiting
   - Add request logging
   - Use HTTPS only
   - Validate all inputs

4. **GitHub Integration**:
   - Use fine-grained tokens
   - Monitor repository creation
   - Implement cleanup procedures

### Scaling

1. **Database**: Migrate to PostgreSQL or MySQL
2. **Caching**: Add Redis for session management
3. **Queue**: Use Celery for background tasks
4. **Monitoring**: Add logging and metrics
5. **Load Balancing**: Use reverse proxy for multiple instances

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all existing tests pass
5. Submit pull request with description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check environment variable configuration
4. Ensure all dependencies are installed

---

*This system implements the complete app build, deploy, and evaluation workflow as specified in the IITM project requirements.*