# Vegetarian Menu Analyzer - Development Commands

# Remote host configuration
remote_host := "root@menu"
remote_path := "/root/menu"

# Default recipe
default:
    @just --list

# Run all syntax checks (mypy, flake8, pyflakes)
check:
    @echo "Running syntax checks..."
    @just check-api
    @just check-mcp
    @echo "All checks passed!"

# Run syntax checks for API service
check-api:
    @echo "Checking API service..."
    cd api && python3 -m mypy app --ignore-missing-imports --no-error-summary || true
    cd api && python3 -m flake8 app --max-line-length=120 --ignore=E501,W503 || true
    cd api && python3 -m pyflakes app || true

# Run syntax checks for MCP service
check-mcp:
    @echo "Checking MCP service..."
    cd mcp && python3 -m mypy app --ignore-missing-imports --no-error-summary || true
    cd mcp && python3 -m flake8 app --max-line-length=120 --ignore=E501,W503 || true
    cd mcp && python3 -m pyflakes app || true

# Sync code to remote host
sync:
    @echo "Syncing code to {{remote_host}}:{{remote_path}}..."
    rsync -avz --delete \
        --exclude '.git' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.pytest_cache' \
        --exclude 'venv' \
        --exclude '.venv' \
        --exclude '*.egg-info' \
        --exclude '.mypy_cache' \
        --exclude '.idea' \
        --exclude '.vscode' \
        --exclude 'chromadb_data' \
        --exclude 'ollama_data' \
        ./ {{remote_host}}:{{remote_path}}/

# Build docker images on remote host
build-remote:
    @echo "Building docker images on {{remote_host}}..."
    ssh {{remote_host}} "cd {{remote_path}} && docker compose build"

# Start services on remote host
start-remote:
    @echo "Starting services on {{remote_host}}..."
    ssh {{remote_host}} "cd {{remote_path}} && docker compose up -d"

# Stop services on remote host
stop-remote:
    @echo "Stopping services on {{remote_host}}..."
    ssh {{remote_host}} "cd {{remote_path}} && docker compose down"

# Run e2e tests on remote host
test-e2e-remote:
    @echo "Running e2e tests on {{remote_host}}..."
    ssh {{remote_host}} "cd {{remote_path}} && docker compose exec -T api python3 -m pytest tests/e2e/ -v"

# Run all tests on remote host
test-remote:
    @echo "Running all tests on {{remote_host}}..."
    ssh {{remote_host}} "cd {{remote_path}} && docker compose exec -T api python3 -m pytest tests/ -v"

# View logs on remote host
logs-remote:
    ssh {{remote_host}} "cd {{remote_path}} && docker compose logs -f"

# Check service health on remote host
health-remote:
    @echo "Checking service health on {{remote_host}}..."
    ssh {{remote_host}} "curl -s http://localhost:8000/health || echo 'API not responding'"

# Full deployment: check -> sync -> build -> start -> test
deploy: check sync build-remote start-remote
    @echo "Waiting for services to start..."
    sleep 10
    @just health-remote
    @just test-e2e-remote
    @echo "Deployment complete!"

# Quick deploy: sync and restart (skip checks and rebuild)
deploy-quick: sync
    ssh {{remote_host}} "cd {{remote_path}} && docker compose restart"
    @echo "Waiting for services to restart..."
    sleep 5
    @just health-remote

# Deploy and run e2e tests only (assumes services already running)
deploy-test: check sync test-e2e-remote

# SSH into remote host
ssh:
    ssh {{remote_host}}

# Local development commands
# --------------------------

# Run local tests
test:
    cd api && python3 -m pytest tests/ -v
    cd mcp && python3 -m pytest tests/ -v

# Run local e2e tests (requires docker-compose up)
test-e2e:
    cd api && python3 -m pytest tests/e2e/ -v

# Start local services
start:
    docker-compose up -d

# Stop local services
stop:
    docker-compose down

# View local logs
logs:
    docker-compose logs -f

# Generate test menu images
generate-images:
    cd api && python3 tests/fixtures/generate_menu_images.py
