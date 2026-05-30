#!/bin/bash
cd /home/ubuntu/real_estate_lead_optimizer
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
