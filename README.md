
HomeHive – AI-Powered Property Search using RAG

HomeHive is an intelligent real estate search application that transforms natural language questions into property insights.
It is built on a Retrieval-Augmented Generation (RAG) architecture, combining structured database querying with semantic understanding.
This allows users to interact conversationally — for example, “Find 3-bedroom homes under 400,000 in low flood risk areas” — and instantly receive accurate, meaningful property listings with explanations.

---

1. PROJECT OVERVIEW

Traditional property search engines rely on keyword filters or rigid parameters.
HomeHive bridges this gap by enabling flexible, human-like queries.
It understands intent, extracts structured filters (like bedrooms, price, flood risk, etc.), executes them against a local property database, and enhances responses with context from semantic embeddings.

The system runs completely locally using Python, FAISS, and SQLite — or can connect to a FastAPI backend for REST API access.
It is optimized for performance, clarity, and easy demonstration.

---

2. MAIN FEATURES

• Natural Language Querying
Users can type questions such as:

* “Show me 2-bedroom apartments under 500k.”
* “Compare the average price between studios and 2-bed flats.”
* “Which area has the highest crime rate?”
  The system automatically interprets and executes these queries.

• Hybrid RAG Pipeline
Combines structured SQL search with vector-based semantic retrieval.
If a query cannot be handled by filters, FAISS similarity search ensures results are still relevant.

• Structured + Semantic Understanding

* SQLite handles filters like price, bedrooms, bathrooms, flood risk, and address.
* FAISS handles text-based matching and meaning similarity.

• Modern Web Interface
Developed in Streamlit, featuring:

* Clean minimal pink-themed interface
* Logo, title banner, and intuitive layout
* Input field and search button
* Example queries to guide users
* Results shown in table or card format
* CSV download options for top 10 or full results

• Data Preprocessing
Raw CSV data is standardized:

* Columns are normalized and cleaned
* Missing values are handled
* Numeric fields are converted correctly
* Output saved to SQLite database and FAISS vector index

---

3. TECHNOLOGIES USED

Frontend: Streamlit – interactive web interface
Backend: Python – main logic and RAG pipeline
Optional API Layer: FastAPI – RESTful interface
Database: SQLite – structured property data
Vector Search: FAISS – fast similarity search engine
Embeddings: SentenceTransformers (all-MiniLM-L6-v2) – converts text to numeric embeddings
Data Handling: Pandas – loading, cleaning, and transformation

---

4. FOLDER STRUCTURE

app.py – Streamlit web application
api.py – FastAPI backend (optional mode)
indexing.py – Builds FAISS vector index and SQLite database

data/
raw/ – contains the original property dataset
processed/ – stores cleaned SQLite database

rag/
embeddings.py – manages FAISS embedding loading and searching
preprocess.py – handles CSV cleaning if needed

src/
config/config.py – defines environment paths and constants
query/parser.py – converts user questions into structured logic
query/executor.py – executes SQL and FAISS queries
query/response_generator.py – formats readable responses and tables
query/schema.py – defines data models and validation logic
rag_pipeline.py – connects all components into the full RAG workflow

requirements.txt – project dependencies
.gitignore – ignored files and folders
README.md – documentation file

---

5. HOW THE SYSTEM WORKS

Step 1: Data Preparation (indexing.py)
Reads the raw dataset, cleans it, and creates:

* SQLite database (properties.db)
* FAISS index (faiss_index.bin)
* Metadata mapping (metadata.pkl)
  Embeddings are generated with SentenceTransformer(all-MiniLM-L6-v2).

Step 2: Query Input (app.py)
User enters a question in Streamlit.
The app passes it to the RAG pipeline for interpretation.

Step 3: Query Parsing (parser.py)
The parser extracts intent and filters:

* Detects bedrooms, bathrooms, price, flood risk, area, etc.
* Classifies the query as FILTER, AGGREGATION, or RETRIEVAL.

Example:
“Show 3-bedroom houses under 400k in low flood risk areas”
→ Query Type: FILTER
→ Bedrooms: 3
→ Price ≤ 400000
→ Flood risk: low

Step 4: Query Execution (executor.py)
Structured queries are executed on SQLite.
If the result is empty, FAISS semantic search retrieves similar entries.
It also handles aggregation queries (AVG, SUM, COUNT, MAX, MIN, COMPARE).

Step 5: Response Generation (response_generator.py)
The raw results are summarized into:

* A narrative (natural text summary)
* A preview table (top 10 results)
* A complete table (all results)

Step 6: Streamlit Display
Results are displayed interactively with download and view options.
Supports both semantic and structured outputs seamlessly.

---

6. RUNNING THE PROJECT

7. Clone the repository
   git clone [https://github.com/salonidembla/homehive.git](https://github.com/salonidembla/homehive.git)
   cd homehive

8. Create and activate a virtual environment
   python -m venv venv
   venv\Scripts\activate (Windows)
   source venv/bin/activate (Mac/Linux)

9. Install dependencies
   pip install -r requirements.txt

10. Build the database and FAISS index (only first time)
    python indexing.py

11. Run the Streamlit app
    streamlit run app.py
    Opens automatically at [http://localhost:8501](http://localhost:8501)

Optional – Run the FastAPI backend
uvicorn api:app --reload
Available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

If faiss_index.bin or metadata.pkl are missing, regenerate them by rerunning indexing.py.

---

7. DATASET

The dataset contains synthetic or public property data with attributes such as:
address, price, bedrooms, bathrooms, type, flood risk, crime score, and description.

Users can replace this dataset with their own CSV, maintaining consistent column names.

---

8. DEMO VIDEO

A detailed demo video of the system workflow and features is available at:
[https://drive.google.com/drive/folders/1294lS3YHn9PNIMJBvxGlMZaJf-_aMCPB](https://drive.google.com/drive/folders/1294lS3YHn9PNIMJBvxGlMZaJf-_aMCPB)

---

9. PROJECT HIGHLIGHTS

• Combines structured SQL queries with semantic FAISS retrieval
• Completely offline and privacy-safe
• Minimal and responsive user interface
• Extensible modular architecture
• Accurate natural language understanding
• Easy reproducibility and scalability
• Professional data pipeline and clean codebase

---

10. FUTURE IMPROVEMENTS

• Integration with OpenAI GPT or Gemini for conversational reasoning
• Dynamic map visualization for geographic results
• User login and favorite listings
• Cloud deployment on AWS EC2 or Streamlit Cloud

---

11. AUTHORS

Developed by: Saloni Dembla
