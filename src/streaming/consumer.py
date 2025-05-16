import logging
import json
import pandas as pd
from kafka import KafkaConsumer
from src.config import KAFKA_BOOTSTRAP, TOPIC, DB_URL
from src.predictor import load_model, predict_df
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

model = load_model()
logger.info("Model loaded successfully")

for msg in consumer:
    logger.info(f"Received message at offset {msg.offset} partition {msg.partition}")
    try:
        features = pd.DataFrame([msg.value])
        pred = predict_df(model, features)
        result_df = features.assign(happiness_pred=pred)
        save_prediction(result_df, DB_URL)
        country = msg.value.get("country")
        year = msg.value.get("year")
        logger.info(f"Saved prediction for {country} ({year})")
    except Exception:
        logger.exception("Error processing message")
