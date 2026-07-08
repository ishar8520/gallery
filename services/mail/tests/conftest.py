import os

os.environ.setdefault('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
os.environ.setdefault('SMTP_HOST', 'localhost')
os.environ.setdefault('SMTP_PORT', '1025')
os.environ.setdefault('SMTP_FROM_EMAIL', 'noreply@gallery.local')
os.environ.setdefault('LINK_SERVICE_URL', 'http://link-service:8000')
os.environ.setdefault('AUTH_PUBLIC_URL', 'http://localhost:8000')
