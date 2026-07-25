# Base image with micromamba preinstalled
FROM mambaorg/micromamba:latest

user root

ARG MAMBA_USER=mambauser

RUN apt-get update && apt-get install -y ssh

user $MAMBA_USER
# Copy environment file
COPY environment.yml /tmp/environment.yml

# Create environment without needing shell activation
RUN micromamba create -y -n twenty48 -f /tmp/environment.yml && \
    micromamba clean --all --yes

# Set environment variables so Python runs without activation
ENV MAMBA_DOCKERFILE_ACTIVATE=1
ENV PATH=/opt/conda/envs/twenty48/bin:$PATH
