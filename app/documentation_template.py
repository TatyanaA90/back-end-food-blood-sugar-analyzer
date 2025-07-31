"""
Documentation template for the Food & Blood Sugar Analyzer API.
This file contains the HTML template for the comprehensive documentation page.
"""

DOCUMENTATION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food & Blood Sugar Analyzer API - Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }
        h2 {
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        .feature-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            border-left: 4px solid #27ae60;
        }
        .auth-section {
            background: #fff3cd;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }
        .code-block {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
            margin: 15px 0;
        }
        ul {
            margin: 15px 0;
            padding-left: 20px;
        }
        li {
            margin: 8px 0;
        }
        .nav-links {
            background: #3498db;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 30px;
        }
        .nav-links a {
            color: white;
            text-decoration: none;
            margin-right: 20px;
            font-weight: 500;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
        .badge {
            background: #e74c3c;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .success-badge {
            background: #27ae60;
        }
        .info-badge {
            background: #3498db;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-links">
            <a href="/docs">Swagger UI</a>
            <a href="/redoc">ReDoc</a>
            <a href="/">API Root</a>
            <a href="/health">Health Check</a>
        </div>
        
        <h1>🍽️ Food & Blood Sugar Analyzer API</h1>
        <p><strong>Version:</strong> <span class="badge">1.0.0</span></p>
        
        <p>A comprehensive API for tracking and analyzing food intake, blood sugar levels, insulin doses, activities, and health conditions for diabetes management.</p>
        
        <h2>🚀 Features</h2>
        
        <div class="feature-section">
            <h3>🔐 Authentication</h3>
            <ul>
                <li>User registration and login with JWT tokens</li>
                <li>Secure password hashing with bcrypt</li>
                <li>Role-based access control (user/admin)</li>
                <li>Automatic token refresh and session management</li>
            </ul>
        </div>
        
        <div class="feature-section">
            <h3>📊 Data Management</h3>
            <ul>
                <li><strong>Glucose Readings:</strong> Track blood sugar levels with unit conversion (mg/dl ↔ mmol/l)</li>
                <li><strong>Meals:</strong> Log meals with ingredients, carbs, and nutritional data</li>
                <li><strong>Activities:</strong> Record exercise with MET-based calorie calculations</li>
                <li><strong>Insulin Doses:</strong> Track insulin injections with meal relationships</li>
                <li><strong>Condition Logs:</strong> Monitor health conditions and symptoms</li>
            </ul>
        </div>
        
        <div class="feature-section">
            <h3>📈 Analytics & Insights</h3>
            <ul>
                <li><strong>Glucose Analytics:</strong> Summary statistics, trends, variability analysis</li>
                <li><strong>Time-in-Range:</strong> Percentage of time spent in target glucose ranges</li>
                <li><strong>Event Analysis:</strong> Hypo/hyperglycemia event detection</li>
                <li><strong>Correlation Analysis:</strong> Meal, activity, and insulin impact on glucose</li>
                <li><strong>AI Recommendations:</strong> Personalized insights and actionable tips</li>
            </ul>
        </div>
        
        <div class="feature-section">
            <h3>📊 Visualization</h3>
            <ul>
                <li><strong>Dashboard Data:</strong> Comprehensive overview with unit conversion</li>
                <li><strong>Timeline Visualization:</strong> Glucose readings with event overlay</li>
                <li><strong>Trend Analysis:</strong> Clean data for chart libraries</li>
                <li><strong>Impact Analysis:</strong> Meal and activity impact data</li>
                <li><strong>Data Quality:</strong> Metrics and recommendations for data improvement</li>
            </ul>
        </div>
        
        <div class="feature-section">
            <h3>🔄 Data Import</h3>
            <ul>
                <li><strong>CSV Upload:</strong> Import CGM data from Dexcom and other devices</li>
                <li><strong>Manual Entry:</strong> Direct data entry for all health metrics</li>
                <li><strong>Bulk Operations:</strong> Efficient data processing for large datasets</li>
            </ul>
        </div>
        
        <h2>🚀 Getting Started</h2>
        <ol>
            <li><strong>Register:</strong> Create a new user account</li>
            <li><strong>Login:</strong> Get your JWT access token</li>
            <li><strong>Upload Data:</strong> Import CSV files or enter data manually</li>
            <li><strong>Analyze:</strong> Use analytics endpoints for insights</li>
            <li><strong>Visualize:</strong> Use visualization endpoints for charts and dashboards</li>
        </ol>
        
        <div class="auth-section">
            <h3>🔑 Authentication</h3>
            <p>Most endpoints require authentication. Include your JWT token in the Authorization header:</p>
            <div class="code-block">
Authorization: Bearer &lt;your_jwt_token&gt;
            </div>
            <p><strong>Token Expiration:</strong> <span class="badge info-badge">30 minutes</span> (configurable)</p>
            <p><strong>Refresh Tokens:</strong> <span class="badge success-badge">Supported</span> for extended sessions</p>
        </div>
        
        <h2>📏 Units</h2>
        <p>The API supports both mg/dl and mmol/l units for glucose values:</p>
        <ul>
            <li><strong>mg/dl:</strong> Traditional US units (default)</li>
            <li><strong>mmol/l:</strong> International units (divide mg/dl by 18)</li>
        </ul>
        <p><strong>Unit conversion is automatic</strong> based on your preference.</p>
        
        <h2>⚡ Rate Limiting</h2>
        <ul>
            <li><strong>Standard endpoints:</strong> <span class="badge">100 requests per minute</span></li>
            <li><strong>Analytics endpoints:</strong> <span class="badge">50 requests per minute</span></li>
            <li><strong>File uploads:</strong> <span class="badge">10 requests per minute</span></li>
        </ul>
        
        <h2>📞 Support</h2>
        <p>For technical support or feature requests, please contact:</p>
        <ul>
            <li><strong>Team:</strong> Food & Blood Sugar Analyzer Team</li>
            <li><strong>Email:</strong> support@foodbloodsugar.com</li>
            <li><strong>License:</strong> MIT License</li>
        </ul>
        
        <h2>🔗 Quick Links</h2>
        <ul>
            <li><a href="/docs">📖 Swagger UI Documentation</a></li>
            <li><a href="/redoc">📚 ReDoc Documentation</a></li>
            <li><a href="/openapi.json">📄 OpenAPI JSON Schema</a></li>
            <li><a href="/">🏠 API Root</a></li>
            <li><a href="/health">💚 Health Check</a></li>
        </ul>
    </div>
</body>
</html>
""" 