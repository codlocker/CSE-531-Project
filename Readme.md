## GENERAL SETUP FOR WINDOWS

1. Install git (version **2.40.1.windows.1**}) [Windows](https://git-scm.com/download/win)
2. Install python version **3.9.13** [Windows](https://www.python.org/downloads/). Ensure python is accessible via [Powershell](https://learn.microsoft.com/en-us/windows/python/beginners)
3. Install pip version **23.2.1**``` py -m ensurepip --upgrade ``` [Source](https://pip.pypa.io/en/stable/installation/)
4. Create a new [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) for pip and install the following packages
   - grpcio==1.59.0
   - grpcio-tools==1.33.2
   - protobuf==3.14.0
5. Activate the newly created environment
6. Clone the repository [CSE-531-Project](https://github.com/codlocker/CSE-531-Project)
   - ```git clone https://github.com/codlocker/CSE-531-Project.git```

## PROJECT 1
---------------------------

### RUN INSTRUCTIONS
1. Run the command ```cd CSE-531-Project/Project 1``` after cloning
2. Run the following the command the build the proto files: ```python -m grpc_tools.protoc -I . .\BankService.proto  --python_out=. --grpc_python_out=.```
3. The entry point of the code is through main.py
   - -i 'Input file path'
   - -o 'Output file path'
   - Example command : python main.py -o output.json -i input.json
  
### RESULTS

- On running the [input.json](./Project%201/input.json), the output is as follows : [output.json](./Project%201/output.json)
- On running the [input1.json](./Project%201/input1.json), the output is as follows : [output1.json](./Project%201/output1.json)

![Project1-result](Project1-Result.png)

## PROJECT 2
---------------------------

### RUN INSTRUCTIONS
1. Run the command ```cd CSE-531-Project/Project 2``` after cloning
2. Run the following the command the build the proto files: ```python -m grpc_tools.protoc -I . .\BankService2.proto  --python_out=. --grpc_python_out=.```
3. The entry point of the code is through main.py and add input.json or any name as the input file 
   - Example command : ```python main.py input.json```

4. To run the checker scripts. Note there are 3 files customer_output.json, branch_output.json and output.json
   - ```python checker_part_1.py customer_output.json```
   - ```python checker_part_2.py branch_output.json```
   - ```python checker_part_3.py output.json```
  
### RESULTS

- Running the checker_scipt for customers we get
![Customer](Project-2-customer-checker.png)

- Running the checker_scipt for branch we get
![Branch](Project-2-branch-checker.png)

- Running the checker_scipt for overall we get
![Overall](Project-2-overall-checker.png)


## PROJECT 3
---------------------------

### RUN INSTRUCTIONS
1. Run the command ```cd CSE-531-Project/Project 3``` after cloning
2. Run the following the command the build the proto files: ```python -m grpc_tools.protoc -I . .\BankService3.proto  --python_out=. --grpc_python_out=.```
3. The entry point of the code is through main.py and add input.json or any name as the input file 
   - Example command : ```python main.py input.json```

4. To run the checker scripts. Note the file is output.json
   - ```python checker.py output.json```
  
### RESULTS

- Running the checker_scipt for small input
![Customer](Project3-input_checker.png)

- Running the checker_scipt for big input
![Branch](Project3-input_big_checker.png)
