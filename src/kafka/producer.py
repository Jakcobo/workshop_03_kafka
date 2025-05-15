import json
import pandas as pd
from kafka import KafkaProducer
from src.config import KAFKA_BOOTSTRAP, TOPIC, COMBINED_CSV

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode()
)

df = pd.read_csv(COMBINED_CSV)
for record in df[feature_cols].to_dict(orient='records'):
    producer.send(TOPIC, record)

producer.flush()
