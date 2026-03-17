import os

def fix_file(filename, content):
    with open(filename, 'wb') as f:
        f.write(content.encode('utf-8').replace(b'\r\n', b'\n'))

docker_content = """FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "1", "--log-file", "-"]
"""

fix_file('Dockerfile', docker_content)

# Remove the lowercase duplicate if it exists
if os.path.exists('dockerfile'):
    os.remove('dockerfile')

print("Dockerfile fixed with strict LF and UTF-8 (No BOM)")
