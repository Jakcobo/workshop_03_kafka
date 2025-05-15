import json
import pandas as pd
from kafka import KafkaConsumer
from src.config import KAFKA_BOOTSTRAP, TOPIC, DB_URL
from src.predictor import load_model, predict_df
from src.db_loader import save_prediction

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda m: json.loads(m)
)

model = load_model()
for msg in consumer:
    features = pd.DataFrame([msg.value])
    pred = predict_df(model, features)
    save_prediction(features.assign(happiness_pred=pred), DB_URL)
