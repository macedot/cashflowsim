#!/bin/bash
mkdir -p ~/.streamlit/
echo -e '
[theme]
base="dark"
[server]
runOnSave=true
maxUploadSize=2000
[browser]
gatherUsageStats = true
' > ~/.streamlit/config.toml
