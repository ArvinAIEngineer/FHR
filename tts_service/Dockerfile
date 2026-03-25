FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

# Set environment
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    espeak-ng > /dev/null 2>&1 \
    && rm -rf /var/lib/apt/lists/*
# Copy files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#RUN python core/tts_voice.py
# Expose port
EXPOSE 443

# Command to run app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "443"]
