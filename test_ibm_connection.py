#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from qiskit_ibm_runtime import QiskitRuntimeService

load_dotenv()
token = os.getenv('IBM_QUANTUM_TOKEN')

print(f"Token loaded: {'Yes' if token else 'No'}")
if token:
    print(f"Token length: {len(token)}")

channels = ['ibm_quantum', 'ibm_cloud']

for ch in channels:
    print(f"\nTesting channel: '{ch}'...")
    try:
        service = QiskitRuntimeService(channel=ch, token=token)
        print(f"✅ Success with channel '{ch}'!")
        print(f"Backends: {[b.name for b in service.backends(simulator=False)[:2]]}") # List first 2 real backends
        break
    except Exception as e:
        print(f"❌ Failed with channel '{ch}': {e}")
