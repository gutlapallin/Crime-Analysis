FROM python:3.11-slim
RUN apt-get update && apt-get install -y openjdk-17-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN mkdir -p /libs && curl -fL -o /libs/mysql-connector-j.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.4.0/mysql-connector-j-9.4.0.jar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY part2_analysis.py .
CMD ["spark-submit", "--driver-memory", "4g", "--jars", "/libs/mysql-connector-j.jar", "part2_analysis.py"]
