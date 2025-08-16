Shopify Store Insights Fetcher Application

A Python application that extracts and structures comprehensive insights from any public Shopify store without utilizing the official Shopify API. Ideal for market research, competitor analysis, and e-commerce trend analysis.(GitHub)

🚀 Features

1.Product Catalog Extraction: Fetches the complete product listings from /products.json.
2.Hero Products Detection: Identifies featured products on the homepage.
3.Policy Extraction: Retrieves privacy, return/refund, and shipping policies.
4.FAQ Extraction: AI-powered FAQ detection and structuring.
5.Contact Information: Extracts email, phone, address, and support hours.
6.Social Media Handles: Identifies Instagram, Facebook, TikTok, etc.
7.Brand Context: About us, mission, founding details.
8.Competitor Analysis: AI-powered competitor discovery and analysis.
9.Persistent Storage: Stores all insights in a MySQL database.
10.Web Interface: Modern web interface with Bootstrap.
11.Deployment Ready: Configured for Render deployment

🛠️ Installation

Clone the repository:(GitHub)

git clone https://github.com/SanchitKulkarni1/Shopify-store-Insights-Fetcher-Application.git
cd Shopify-store-Insights-Fetcher-Application

()

Create and activate a virtual environment:(GitHub)

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

()

Install dependencies:(GitHub)

pip install -r requirements.txt

()

Configure the database (optional):

Edit .env file to use MySQL instead of SQLite.

Uncomment and modify the DATABASE_URL line.(GitHub)

🧪 Usage

To run the application locally:()

uvicorn src.main:app --reload

()

Access the API documentation at:
http://localhost:8000/docs()

To fetch insights from a Shopify store:(GitHub)

curl -X 'POST' \
  'http://localhost:8000/api/v1/insights' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "website_url": "https://example-store.myshopify.com"
}'

()

Replace "https://example-store.myshopify.com" with the desired Shopify store URL.(GitHub)

🗂️ Project Structure

shopify-insights-app/
├── src/
│   ├── main.py               # Entry point of the application
│   ├── api/                  # API endpoints for various data
│   │   ├── products.py       # Product-related endpoints
│   │   ├── policies.py       # Policy-related endpoints
│   │   ├── faqs.py           # FAQ-related endpoints
│   │   ├── social.py         # Social media endpoints
│   │   └── contact.py        # Contact information endpoints
│   ├── services/             # Services for data fetching and organization
│   │   ├── shopify_client.py # Shopify client for API requests
│   │   └── data_organizer.py # Data organization logic
│   ├── models/               # Data models for validation
│   │   └── schemas.py        # Pydantic schemas
│   └── utils/                # Utility functions
│       └── helpers.py        # Helper functions for data handling
├── requirements.txt          # Project dependencies
├── README.md                 # Project documentation
└── .gitignore                # Files to ignore in version control

()

🤝 Contributing

Contributions are welcome! Please follow these steps:()

Fork the repository.

Create a new branch (git checkout -b feature-branch).

Make your changes.

Commit your changes (git commit -am 'Add new feature').

Push to the branch (git push origin feature-branch).

Create a new Pull Request.()

