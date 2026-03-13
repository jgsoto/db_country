# Country Detection Pipeline for Social Media Locations

## Overview

This project processes social media records stored in PostgreSQL and determines the **country of origin** from the `location` field.

The detected country is stored as an **ISO3 country code**.

The pipeline performs two operations:

1. **Country detection**  
   Determines the country from the `location` field and stores it in `salert_basic.country`.

2. **Post synchronization**  
   After each processed hour, the detected country is copied into `salert_post_temp.pais` for related posts.

The system processes records **starting from the most recent dates** and works in **hourly batches** to improve performance, consistency, and recovery in case of failure.

---

# Project Structure


project/
│
├── conexion_bd.py # PostgreSQL connection
├── country_ia.py # AI inference for country detection
├── country_clean.py # Location cleaning and validation
├── Determinate_country.py # Main pipeline script
├── Country_post.py # Post country synchronization
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env


---

# Pipeline Architecture


location
↓
text cleaning
↓
location validation
↓
direct country detection (pycountry)
↓
AI inference (Groq LLM)
↓
ISO3 country code
↓
stored in salert_basic.country
↓
hourly synchronization
↓
stored in salert_post.pais


---

# Processing Strategy

The pipeline processes data using the following strategy:

- **Most recent dates first**
- **Hourly processing batches**
- **Commit after each hour**
- **Post synchronization after each hour**

This approach ensures:

- Reduced memory usage
- Better error recovery
- Incremental data updates
- Reliable long-running execution

---

# Scripts

## 1. Determinate_country.py

Main pipeline script.

This script:

1. Retrieves dates with pending country detection.
2. Processes records **from the most recent date to the oldest**.
3. Splits records into **hourly batches**.
4. Cleans and analyzes the `location` field.
5. Determines the country using a multi-step strategy.
6. Updates `salert_basic.country`.
7. Synchronizes related posts in `salert_post`.

Table updated:


public.salert_basic


Detection strategy:

1. Location cleaning
2. Location validation
3. Direct detection using `pycountry`
4. AI inference using Groq LLM

If the country cannot be determined, the value:


UNK


is stored.

---

## 2. country_post.py

Synchronizes the detected country into the related posts table.

Updates:


public.salert_post_temp.pais


Using the relationship:


salert_post_temp.page_id = salert_basic.id


This ensures that posts inherit the country already determined for their page.

---

# Environment Variables

Create a `.env` file with the following variables:


DB_HOST=localhost
DB_NAME=database_name
DB_USER=username
DB_PASS=password
DB_PORT=5432

GROQCLOUD_API_KEY=your_api_key

---

# Installation

Clone the repository:


git clone <repo_url>
cd project


Create a virtual environment:


python -m venv venv


Activate it:

**Windows**


venv\Scripts\activate


**Linux / Mac**


source venv/bin/activate


Install dependencies:


pip install -r requirements.txt


---

# Running the Pipeline

Run the main pipeline:


python Determinate_country.py


This script will:

1. Detect countries from `location`
2. Update `salert_basic.country`
3. Synchronize results to `salert_post.pais`

---

# Running with Docker

Build and run the container:


docker compose up --build


The container will execute the pipeline automatically.

---

# Features

- ISO3 country detection
- Location text cleaning
- AI fallback for ambiguous locations
- In-memory cache to reduce AI calls
- Hourly batch processing
- Processes **most recent records first**
- Automatic synchronization of related posts
- PostgreSQL integration
- Docker support

---

# Dependencies

- psycopg2
- python-dotenv
- pycountry
- openai

---

# Example Output


Procesando fecha: 2025-07-17
Horas con registros: 2

Procesando hora: 2025-07-17 15:00:00
Registros encontrados: 3

Procesando: Madrid
ISO3: ESP

Procesando: Guayaquil
ISO3: ECU

Commit realizado para la hora 2025-07-17 15:00:00
Sincronización completada