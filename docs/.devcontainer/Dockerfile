FROM mcr.microsoft.com/devcontainers/base:jammy

RUN apt-get update && \
    apt-get -y install --no-install-recommends \
    texlive-full=2021.20220204-1 \
    biber=2.17-2 \
    python3=3.10.6-1~22.04 \
    python3-pygments=2.11.2+dfsg-2 \
    ttf-bitstream-vera=1.10-8.2 && \
    rm -rf /var/lib/apt/lists/*

# installing cpanm & missing latexindent dependencies
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -L http://cpanmin.us | perl - --self-upgrade && \
    cpanm Log::Dispatch::File YAML::Tiny File::HomeDir
