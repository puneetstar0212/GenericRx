# GenericRx

**GenericRx** is a modern, offline-first web application designed to help users discover generic medicine alternatives, calculate prescription cost savings, and locate nearby pharmacies and Jan Aushadhi Kendras. 

Built as a Progressive Web App (PWA) with a Python FastAPI backend, GenericRx is designed to work reliably even in zero-connectivity environments like remote clinics.

---

## 🌟 Key Features

*   **Intelligent Medicine Search**: Fuzzy search through an extensive database of 650+ medicines by brand name (e.g., Crocin, Augmentin) or active chemical salt (e.g., Paracetamol).
*   **Generic Alternatives**: Instantly maps expensive branded drugs to affordable, government-approved Jan Aushadhi generic equivalents.
*   **Prescription Cost Savings Audit**: Add multiple medications to an audit basket to calculate estimated monthly and annual cost savings when switching to generics.
*   **Offline-First Architecture**: Utilizes Service Workers and IndexedDB (via Dexie.js) to cache the medicine catalog and allow 100% offline search and audit capabilities.
*   **Interactive Pharmacy Locator**: 100% free OpenStreetMap and Leaflet.js integration to locate nearby retail pharmacies and Jan Aushadhi Kendras.
*   **Modern Glassmorphism UI**: Beautiful, responsive, futuristic UI with neon glows, micro-animations, and animated statistics counters.

## 🛠️ Technology Stack

*   **Backend**: Python, FastAPI, SQLite, SQLAlchemy, RapidFuzz
*   **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript
*   **Offline Layer**: Service Workers, Web App Manifest, IndexedDB (Dexie.js), Fuse.js
*   **Mapping**: Leaflet.js & OpenStreetMap

## 🚀 How to Run Locally

### Prerequisites
*   Python 3.8+ installed on your system.

### Installation

1.  **Clone or navigate to the project directory:**
    ```bash
    cd path/to/genericrx
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate and Seed the Database:**
    *The dataset generator will create over 650 records and seed them into a local SQLite database (`genericrx.db`).*
    ```bash
    python -m app.seed_database
    ```

4.  **Start the Server:**
    ```bash
    python run.py
    ```

5.  **Access the Application:**
    Open your web browser and navigate to:
    👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## 📚 API Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can explore the REST endpoints at:
*   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## ⚠️ Regulatory Disclaimer

GenericRx is a neutral educational and price audit tool. Controlled drugs marked Schedule H or Schedule X require a valid doctor's prescription. Never alter your dosage strength or active chemical composition without prior consultation with a qualified medical professional or pharmacist.
