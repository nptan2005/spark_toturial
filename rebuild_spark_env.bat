@echo off
conda deactivate
conda remove --name spark_env --all -y
conda env create -f environment.yml
conda activate spark_env
pause
