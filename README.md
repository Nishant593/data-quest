## **Data Sync Assignment**

##### **_Features_**
1. Automated BLS CSV Fetching
2. Automated API data Fetching
3. Data cleaning
4. Analysis of data

##### **_Technologies Used_**
1. Localstack (Local AWS service Simulator)
2. Python 3.11 (Lambdas are written in Python)
3. Pandas
4. Jupyter Notebook (Used to analyse the data)

##### **_Steps to Deploy locally_**
1. Install Localstack in your system. (I am running the localstack on docker)
   Command to run the localstack on docker
   ```
   docker run -d -p 4566:4566 -p 4571:4571 -e SERVICES=lambda,s3,iam,logs,events -e DEBUG=1 -e LAMBDA_EXECUTOR=docker-reuse -v //var/run/docker.sock:/var/run/docker.sock --name localstack localstack/localstack
   ```
3. Create the terraform for creating resources like s3 bucket, lambdas, eventbridge, logs
4. The following code will help package the lambda codes.
    ```
    mkdir lambda_build
    cd lambda_build
    copy ..\lambda\lambda_function.py .
    pip install -r ..\lambda\requirements.txt -t .
    powershell Compress-Archive -Path * -DestinationPath ..\lambda_function.zip
    cd ..
   ```
5. Run terraform commands to deploy the project.
    ```
    terraform init --upgrade
    terraform apply -auto-approve
    ```
6. The following command is needed to run the lambda.
    ```
    aws --endpoint-url=http://localhost:4566 lambda invoke --function-name data-sync-lambda output.json
    ```
