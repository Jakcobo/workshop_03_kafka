# Workshop 03: Kafka Streaming Happiness Index

This repository demonstrates an end-to-end pipeline for:

1. **Ingesting** five annual CSVs of country-level happiness data (2015–2019)
2. **Exploratory Data Analysis (EDA)** and feature engineering
3. **Training** a Random Forest regression model to predict the happiness score
4. **Streaming** the preprocessed features via Kafka (producer)
5. **Consuming** the stream (consumer), applying the trained model, and **storing** predictions in PostgreSQL
6. **Containerizing** everything with Docker / Docker Compose for easy reproducibility

---

## 🚀 Quick Start

1. **Clone the repo**

   ```bash
   git clone https://github.com/jakcobo/workshop_03_kafka.git
   cd workshop_03_kafka
   ```

2. **Fill out your `.env`** (an example is provided):

   ```dotenv
   # PostgreSQL
   DB_USER=postgres
   DB_PASS=postgres
   DB_NAME=happiness_db
   DB_HOST=postgres
   DB_PORT=5432

   # Kafka
   KAFKA_BOOTSTRAP=kafka:9092
   TOPIC=happiness_features

   # Data
   COMBINED_CSV=data/combined_happiness.csv
   ```

3. **Build and run all services**

   ```bash
   docker compose down -v
   docker compose up --build 
   ```

4. **Verify**

   * **Producer logs**

     ```bash
     docker compose logs --follow app-producer
     # should see: "Sent 781 records to happiness_features"
     ```
   * **Consumer logs**

     ```bash
     docker compose logs --follow app-consumer
     # should see offsets processed one by one and "Saved prediction…" lines
     ```
   * **Database**

     ```bash
     docker compose exec postgres psql -U $DB_USER -d $DB_NAME
     \dt
     SELECT COUNT(*) FROM predictions;   -- expect 781
     SELECT * FROM predictions LIMIT 5;
     \q #for go out of terminal
     ```

---

## 🛠️ Technologies & Libraries

* **Data processing & ML:** Python 3.11, pandas, scikit-learn, category-encoders, xgboost, joblib
* **Streaming:** Apache Kafka (Confluent cp-kafka), ZooKeeper, kafka-python
* **Database:** PostgreSQL, SQLAlchemy, psycopg2-binary
* **Containerization:** Docker, Docker Compose
* **Notebook tooling:** JupyterLab, matplotlib, seaborn

---

## 🔄 Pipeline Overview

1. **EDA & ETL** (`notebooks/001_eda_&_clean.ipynb`)

   * Load and merge the five annual CSVs
   * Clean and unify column names
   * Feature-engineer:

     * Add `year`
     * Map `country → continent`
     * Create `gdp_support = gdp_per_capita * social_support`
   * Export `data/combined_happiness.csv` for training & streaming

2. **Model Training** (`notebooks/002_model.ipynb`)

   * Define `feature_cols = ['freedom','gdp_per_capita','healthy_life_expectancy','social_support','generosity','trust_government_corruption','year','continent','gdp_support']`
   * Train/test split (70/30)
   * One-hot encode `continent` and `year` (drop first level, align train/test)
   * Compare algorithms (Linear, Ridge, Lasso, RandomForest, GBM)
   * Select **RandomForest** (R²≈0.85, MAE≈0.32)
   * Persist pipeline to `model_rf/model_random_forest.pkl`

3. **Producer** (`src/streaming/producer.py`)

   * Reads `data/combined_happiness.csv`
   * Streams each row as JSON to Kafka topic `happiness_features`

4. **Consumer** (`src/streaming/consumer.py`)

   * Subscribes to `happiness_features` (group `happiness_consumer_group`)
   * `max_poll_records=1` + `time.sleep(1)` for paced output
   * For each message:

     1. Recompute any missing features (`gdp_support`)
     2. One-hot encode `continent` & `year` (drop first level)
     3. Align columns to the trained pipeline’s `feature_names_in_`
     4. Predict with `pipeline.predict(X)`
     5. Save features + `happiness_pred` to PostgreSQL via `src/db_loader.py`

5. **Database** (`src/db_loader.py`)

   * Uses SQLAlchemy to `to_sql('predictions', engine, if_exists='append')`
   * Automatically creates the table on first insert

6. **Orchestration**

   * **Dockerfile** builds a Python image with dependencies, code, data (or mounts via volumes)
   * **docker-compose.yml** brings up:

     * zookeeper
     * kafka (Confluent cp-kafka, healthchecked)
     * postgres (with named volume)
     * app-producer & app-consumer (linked by `depends_on` and health conditions)

---

## 📁 Repository Structure

```
workshop_03_kafka/
├── data/
│   └── combined_happiness.csv       # preprocessed CSV from EDA
├── model_rf/
│   └── model_random_forest.pkl      # trained pipeline
├── notebooks/
│   ├── 001_eda_&clean.ipynb                 # data exploration & feature engineering
│   └── 002_model.ipynb       # feature selection, training, evaluation
├── src/
│   ├── config.py                    # environment & connection settings
│   ├── predictor.py                 # load_model(), predict_df()
│   ├── db_loader.py                 # save_prediction() to PostgreSQL
│   └── streaming/
│       ├── __init__.py
│       ├── producer.py              # Kafka producer
│       └── consumer.py              # Kafka consumer + prediction
├── Dockerfile                       # builds the Python image
├── docker-compose.yml               # orchestrates Kafka, Postgres, producer, consumer
├── requirements.txt                 # Python deps
├── .env                             # environment variables (not committed)
└── README.md                        # you are here
```

---

## 📝 Notes & Tips

* **Volume mounting** of `./data` (and optionally `./model_rf`) in Compose lets you update CSV or model without rebuilding the image.
* Use `docker compose logs --follow` to tail logs for both producer and consumer.
* Offset management (`group_id`, `auto_offset_reset='earliest'`) ensures **exactly-once** processing for each message group.
* You can extend this pattern to multiple topics, services, or even other message brokers (RabbitMQ, AWS MSK, etc.).
