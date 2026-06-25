FROM python:3.11-slim

# working directory
WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the script
COPY elt.py .

# Default command (what runs when Airflow starts the container)
CMD ["python", "elt.py"]