#################### Constants
end_line = f"\n{'#'*80}\n"

#################### System Paths
import sys
py_path = sys.path
print("PYTHONPATH", py_path, sep="\n", end=end_line)
help("modules")
print("Available modules", sep="\n", end=end_line)

#################### Package Structure
for indx in [1, 2]:
    print(f"Showing the Package `{py_path[indx]}` Structure:")
    import zipfile
    with zipfile.PyZipFile(py_path[indx], mode="r") as zip_pkg:
        zip_pkg.printdir()
    print("", end=end_line)

#################### Arguments for the scripts
print(f"Parsing the arguments:")
import argparse
parser = argparse.ArgumentParser(description='Test inputs.')
parser.add_argument('positional_arg')
parser.add_argument('--optional_arg', default='default_value')
args = parser.parse_args()
print(f"The given args are:", args, sep="\n", end=end_line)

#################### Import modules from the code base
print("Import `User` in `my_class` from `my_module`")
from my_module.my_class import User
print("Create a `User` in the `main.py` module")
user = User(
    id="01",
    user="user_1",
    num="1",
    date="2020-1-1",
)
print(user, sep="\n", end=end_line)

#################### Import modules from the requirements
print("Import the `requests` module")
import requests
print(requests, sep="\n", end=end_line)

if __name__ == "__main__":
    #################### Main pyspark app
    print("Running the main program")
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("my_test").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    # input_path = "/Users/cesar.pina/Desktop/test_emr_serverless/data/test.csv"
    input_path = "s3://civanpima-emr-serverless-bucket/test_emr_serverless/data"
    df = spark.read.csv(input_path, header=True)
    print(f"Users data count: {df.count()}", sep="\n", end=end_line)

