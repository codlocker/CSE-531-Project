### SETUP FOR WINDOWS

1. Install git [Windows](https://git-scm.com/download/win)
2. Install python [Windows](https://www.python.org/downloads/). Ensure python is accessible via [Powershell](https://learn.microsoft.com/en-us/windows/python/beginners)
3. Install pip ``` py -m ensurepip --upgrade ``` [Source](https://pip.pypa.io/en/stable/installation/)
4. Create a new [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) for pip and install the following packages
   - grpcio==1.59.0
   - grpcio-tools==1.33.2
   - protobuf==3.14.0
5. Activate the newly created environment
6. Unzip the code files and cd to the directory which has 'main.py' and the '.proto' file

### RUN INSTRUCTIONS
1. Run the following the command the build the proto files: ```python3 -m grpc_tools.protoc -I . .\BankService.proto  --python_out=. --grpc_python_out=.```
2. The entry point of the code is through main.py
   - -i 'Input file path'
   - -o 'Output file path'
   - Example command : python .\main.py -o output.json -i input.json
  
### RESULTS

- On running the [input.json](https://github.com/codlocker/CSE-531-Project/blob/develop/Project%201/input.json), the output is as follows : [output.json](https://github.com/codlocker/CSE-531-Project/blob/develop/Project%201/output.json)
- On running the [input1.json](https://github.com/codlocker/CSE-531-Project/blob/develop/Project%201/input1.json), the output is follows : [output1.json](https://github.com/codlocker/CSE-531-Project/blob/develop/Project%201/output1.json) 
