# Use Python 3.10 as base image
FROM python:3.10

# Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy the requirements file from the parent directory into the container
# COPY ../requirements.txt /app/
COPY ../requirements.txt .

# Install dependencies
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django app into the container
# COPY . /app/
COPY . .

# Expose the Django port
EXPOSE 8000

# ALX checker hint: run with -p 8000:8000
# Run Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
