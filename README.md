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


# Summary of what was done

## 1. Data Ingestion & Cleaning  
- **Load five annual CSVs (2015–2019)** into separate DataFrames.  
- **List and reconcile all column names** using fuzzy matching to detect typos and variants.  
- **Standardize column names** (e.g. `Happiness.Score`, `Score` → `happiness_score`) via a mapping dictionary.  
- **Merge yearly DataFrames** into a single table, aligning all columns and adding a `year` column.  
- **Drop irrelevant columns** (`standard_error`, confidence intervals, `dystopia_residual`, `region`) and remove rows missing `trust_government_corruption`.  

## 2. Exploratory Data Analysis (EDA)  
- **Data structure:** Confirmed 781 rows × 10 core columns (one object, nine numeric).  
- **Descriptive statistics:** Computed means, standard deviations, ranges and quartiles for all numeric features.  
- **Distributions:** Plotted histograms to reveal skewness—GDP, life expectancy and social support right-skewed; generosity and corruption trust heavily right-skewed.  
- **Correlation heatmap:** Identified strong positive links among GDP, life expectancy and happiness; moderate links for freedom and social support; weak links for generosity and corruption trust.  
- **Pairwise scatterplots:** Verified linear, positively sloped relationships of GDP, health, social support and freedom with happiness.  
- **Yearly boxplots:** Observed gradual year-to-year improvements in GDP, life expectancy, social support and freedom; generosity and corruption trust remained more variable.  

## 3. Feature Engineering  
- **Continent**: Mapped each country to its continent to capture regional effects.  
- **Interaction term**: Created `gdp_support = gdp_per_capita × social_support` to model synergistic impacts.  

## 4. Model Preparation  
- **Feature matrix (X) and target (y)**: Selected eight core predictors plus engineered features (`continent`, `year`, `gdp_support`).  
- **Train–test split**: 70% training, 30% testing with fixed random seed for reproducibility.  
- **One-hot encoding**: Transformed categorical `continent` and `year` into indicator variables; aligned train and test sets.  

## 5. Model Training & Comparison  
Trained and evaluated five regression pipelines (all scaled via StandardScaler):  
1. **Linear Regression** — MAE 0.365, R² 0.803  
2. **Lasso Regression** — MAE 0.424, R² 0.767  
3. **Gradient Boosting** — MAE 0.338, R² 0.847  
4. **XGBoost** — MAE 0.348, R² 0.833  
5. **Random Forest** — MAE 0.323, R² 0.852  

## 6. Final Model Selection  
- **Random Forest** outperformed all competitors with the lowest MAE (0.323) and highest R² (0.852), balancing accuracy and robustness.  
- Chosen as the production model for predicting `happiness_score`.

---

**Overall Conclusion:**  
Through systematic cleaning, thorough EDA, targeted feature engineering and rigorous model comparison, we identified Random Forest as the optimal algorithm for forecasting national happiness scores using socio-economic and regional indicators.  
