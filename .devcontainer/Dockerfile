FROM mcr.microsoft.com/devcontainers/base:bookworm

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    software-properties-common \
    build-essential \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install pip-tools for lockfile management
RUN pip3 install --no-cache-dir pip-tools

# Install Docker Compose v2
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Install kubectl
RUN curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | gpg --dearmor -o /usr/share/keyrings/kubernetes-apt-keyring.gpg && \
    echo 'deb [signed-by=/usr/share/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update && apt-get install -y kubectl && rm -rf /var/lib/apt/lists/*

# Install kustomize
RUN curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash && \
    mv kustomize /usr/local/bin/

# Install cosign for image signing
RUN curl -LO https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 && \
    chmod +x cosign-linux-amd64 && \
    mv cosign-linux-amd64 /usr/local/bin/cosign

# Set up Python path for workspace
ENV PYTHONPATH=/workspace/value-fabric/layer1-ingestion/src:/workspace/value-fabric/layer2-extraction/src:/workspace/value-fabric/layer3-knowledge/src:/workspace/value-fabric/layer4-agents/src:/workspace/value-fabric/layer5-ground-truth/src:/workspace/value-fabric/layer6-benchmarks/src

# Default working directory
WORKDIR /workspace
