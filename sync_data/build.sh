mkdir lambda_build
cd lambda_build
copy ..\lambda\lambda_function.py .
pip install -r ..\lambda\requirements.txt -t .
cd ..