# src/streaming/producer.py

import json
import pandas as pd
import logging
from kafka import KafkaProducer
from src.config import KAFKA_BOOTSTRAP, TOPIC, COMBINED_CSV

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
feature_cols = [
    'freedom',
    'gdp_per_capita',
    'healthy_life_expectancy',
    'social_support',
    'generosity',
    'trust_government_corruption',
    'year',
    'continent',
    'gdp_support'
]

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode()
)

df = pd.read_csv(COMBINED_CSV)
df_features = df[feature_cols]

records = df_features.to_dict(orient='records')
for record in records:
    producer.send(TOPIC, record)

producer.flush()
logger.info(f'Sent {len(records)} records to {TOPIC}')
