#!/bin/bash
# Post-create script for devcontainer setup

set -e

echo "🔧 Setting up Value Fabric development environment..."

# Navigate to workspace
cd /workspace

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
if [ -f "pnpm-lock.yaml" ]; then
    pnpm install --frozen-lockfile
else
    pnpm install
fi
cd ..

# Install Python dependencies for all layers
echo "🐍 Installing Python dependencies for all layers..."
for layer_dir in value-fabric/layer*/; do
    if [ -f "$layer_dir/pyproject.toml" ]; then
        layer_name=$(basename "$layer_dir")
        echo "  → Installing $layer_name..."
        cd "$layer_dir"
        
        # Create virtual environment if it doesn't exist
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
        fi
        
        # Activate and install
        source .venv/bin/activate
        if [ -f "requirements-dev.lock" ]; then
            pip install -r requirements-dev.lock
        else
            pip install -e ".[dev]"
        fi
        deactivate
        
        cd /workspace
    fi
done

# Set up pre-commit hooks if pre-commit is available
if command -v pre-commit &> /dev/null; then
    echo "🪝 Setting up pre-commit hooks..."
    pre-commit install
fi

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Quick start commands:"
echo "  make dev-up        # Start all services with docker-compose"
echo "  make test          # Run all tests"
echo "  make lint          # Run linting"
echo "  cd frontend && pnpm dev  # Start frontend dev server"
echo ""
