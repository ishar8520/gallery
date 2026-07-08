import os

os.environ.setdefault('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
os.environ.setdefault('SMTP_HOST', 'localhost')
os.environ.setdefault('SMTP_PORT', '1025')
os.environ.setdefault('SMTP_FROM_EMAIL', 'noreply@gallery.local')
