FROM python:3.11-slim-bookworm
ENV TZ=Asia/Shanghai MPLBACKEND=Agg QUANT_EXECUTION_MODE=local-paper
WORKDIR /workspace/quant-research-cloud
COPY scripts/system.sh /tmp/quant-system.sh
RUN bash /tmp/quant-system.sh && rm -rf /var/lib/apt/lists/*
COPY . .
ARG QUANT_PROFILE=all
RUN INSTALL_SYSTEM_PACKAGES=0 INSTALL_BROWSER_DEPS=1 bash scripts/setup.sh "$QUANT_PROFILE"
ENV PATH="/workspace/quant-research-cloud/.venv/bin:${PATH}"
CMD ["bash", "scripts/start.sh"]
