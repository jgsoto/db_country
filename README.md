# Country Detection Pipeline for Social Media Locations

## Overview

This project processes social media records stored in PostgreSQL and determines the **country of origin** from the `location` field.

The detected country is stored as an **ISO3 country code**.

The pipeline works in two stages:

1. **Country detection**
   Determines the country from the `location` field and stores it in `salert_basic.country`.

2. **Post synchronization**
   Copies the detected country into the `salert_post_temp.pais` field for related posts.

The system processes records **starting from the most recent dates** and works in **hourly batches** for efficiency and reliability.

---

# Project Structure

```
project/
│
├── conexion_bd.py
├── country_ia.py
├── country_clean.py
├── procesar_locations.py
├── sincronizar_post.py
├── requirements.txt
└── .env
```

---

# Pipeline Architecture

```
location
   ↓
cleaning & validation
   ↓
direct country detection (pycountry)
   ↓
AI inference (Groq LLM)
   ↓
ISO3 country code
   ↓
stored in salert_basic.country
   ↓
synchronized to salert_post_temp.pais
```

---

# Scripts

## 1. procesar_locations.py

Detects the country from the `location` field and updates the table:

```
public.salert_basic
```

Steps:

1. Find records where `country IS NULL`
2. Process **most recent dates first**
3. Split processing **by hour**
4. Clean and analyze `location`
5. Detect country
6. Update `country` column

Detection strategy:

1. Clean text
2. Validate location
3. Direct detection using `pycountry`
4. AI inference using Groq LLM

---

## 2. sincronizar_post.py

Copies the detected country to the related posts table.

Updates:

```
public.salert_post_temp.pais
```

Using:

```
salert_post_temp.page_id = salert_basic.id
```

This ensures posts inherit the country already determined for their page.

---

# Environment Variables

Create a `.env` file with the following variables:

```
DB_HOST=localhost
DB_NAME=database_name
DB_USER=username
DB_PASS=password
DB_PORT=5432

GROQCLOUD_API_KEY=your_api_key
```

---

# Installation

Clone the repository:

```
git clone <repo_url>
cd project
```

Create virtual environment:

```
python -m venv venv
```

Activate it:

Windows:

```
venv\Scripts\activate
```

Linux / Mac:

```
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# Usage

## Step 1 — Detect countries

```
python procesar_locations.py
```

This will populate:

```
salert_basic.country
```

---

## Step 2 — Synchronize posts

```
python sincronizar_post.py
```

This will populate:

```
salert_post_temp.pais
```

---

# Features

* ISO3 country detection
* Location text cleaning
* AI fallback for ambiguous locations
* In-memory cache to reduce AI calls
* Processing by **hour batches**
* Processes **most recent records first**
* PostgreSQL integration

---

# Dependencies

* psycopg2
* python-dotenv
* pycountry
* openai

---

# Example Output

```
Procesando fecha: 2025-07-17
Horas con registros: 2

Procesando hora: 2025-07-17 15:00:00
Registros encontrados: 3

Procesando: Madrid
ISO3: ESP

Procesando: Guayaquil
ISO3: ECU
```

---

# Author

Data pipeline for automated **country inference from social media locations**.
