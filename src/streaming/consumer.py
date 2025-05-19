import logging
import json
import time
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
    enable_auto_commit=True,
    max_poll_records=1
)
logger.info(f"Subscribed to topic {TOPIC}")

pipeline = load_model()
logger.info("Model pipeline loaded")

expected_cols = list(pipeline.feature_names_in_)

for msg in consumer:
    logger.info(f"Received message at offset {msg.offset}")
    try:
        record = msg.value
        df_msg = pd.DataFrame([record])
        df_msg['gdp_support'] = df_msg['gdp_per_capita'] * df_msg['social_support']
        df_enc = pd.get_dummies(df_msg, columns=['continent', 'year'], drop_first=True)
        X = df_enc.reindex(columns=expected_cols, fill_value=0)
        pred = pipeline.predict(X)
        out = X.copy()
        out['happiness_pred'] = pred
        save_prediction(out, DB_URL)
        logger.info(f"Saved prediction for {record.get('country')} ({record.get('year')})")
    except Exception:
        logger.exception("Error processing message")
    time.sleep(1)
