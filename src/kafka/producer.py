import json
import pandas as pd
import logging
from kafka import KafkaConsumer
from src.config import KAFKA_BOOTSTRAP, TOPIC, DB_URL
from src.predictor import load_model, predict_df
from src.db_loader import save_prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

model = load_model()
logger.info('Consumer started and model loaded')

for msg in consumer:
    record = msg.value
    features_df = pd.DataFrame([record])
    pred = predict_df(model, features_df)
    features_df['happiness_pred'] = pred
    save_prediction(features_df, DB_URL)
    logger.info(f"Saved prediction for {record.get('country')} ({record.get('year')})")
