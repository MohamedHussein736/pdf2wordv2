# Use the official Python base image
FROM python:3.8 

# Update system packages
RUN apt-get update && apt-get install -y libssl-dev && apt-get install -y apt-utils
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

RUN dpkg -i libssl1.1_1.1.1f-1ubuntu2.19_amd64.deb

# Expose the port that Uvicorn will run on
EXPOSE 8000

# Define the command to run your Uvicorn app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]

