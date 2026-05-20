@echo off

cd /d E:\Project 619\event_management_system\uems

C:\Users\LAPTOP STORE\AppData\Local\Programs\Python\Python314\python.exe manage.py mark_absent

echo %date% %time% >> logs.txt
echo mark_absent executed >> logs.txt