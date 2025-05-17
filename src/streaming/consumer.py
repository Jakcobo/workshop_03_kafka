# src/streaming/consumer.py

import logging
import json
import pandas as pd
from kafka import KafkaConsumer
from src.config import KAFKA_BOOTSTRAP, TOPIC, DB_URL
from src.predictor import load_model
from src.db_loader import save_prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Consumer starting up")
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda m: json.loads(m),
    group_id='happiness_consumer_group',
    auto_offset_reset='earliest',
    enable_auto_commit=True
)
logger.info(f"Subscribed to topic {TOPIC}")

pipeline = load_model()
logger.info("Model pipeline loaded")

# get the feature names expected by the pipeline
expected_cols = list(pipeline.feature_names_in_)

for msg in consumer:
    offset = msg.offset
    logger.info(f"Received message at offset {offset}")
    try:
        record = msg.value
        df_msg = pd.DataFrame([record])

        # 1) Create any interaction features if your EDA did so
        df_msg['gdp_support'] = (
            df_msg['gdp_per_capita'] * df_msg['social_support']
        )

        # 2) One-hot encode continent & year, drop first level
        df_enc = pd.get_dummies(
            df_msg,
            columns=['continent','year'],
            drop_first=True
        )

        # 3) Align to expected pipeline inputs
        X = df_enc.reindex(columns=expected_cols, fill_value=0)

        # 4) Predict
        pred = pipeline.predict(X)

        # 5) Save only the features + prediction
        out = X.copy()
        out['happiness_pred'] = pred
        save_prediction(out, DB_URL)

        logger.info(f"Saved prediction for {record.get('country')} ({record.get('year')})")

    except Exception:
        logger.exception("Error processing message")
