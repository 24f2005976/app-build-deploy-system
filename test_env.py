import sys
import os
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Python path:", sys.executable)
print("Files in current directory:", os.listdir("."))
if os.path.exists("student_api"):
    print("Files in student_api:", os.listdir("student_api"))
else:
    print("student_api directory not found")