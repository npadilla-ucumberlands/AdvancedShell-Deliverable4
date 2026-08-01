# Advanced Shell - Deliverable 4: Final Integration and Security Implementation

## Overview

This repository contains **Deliverable 4** of the Advanced Shell project for **MSCS 630 – Advanced Operating Systems** at the University of the Cumberlands.

The objective of this deliverable was to integrate all components developed during the previous deliverables into a single cohesive shell while implementing advanced operating system features including command piping, user authentication, and role-based file permissions.

The completed shell demonstrates practical implementations of core operating system concepts including process management, CPU scheduling, virtual memory management, process synchronization, command piping, authentication, and access control.

---

## Features

### Deliverable 1

- Built-in shell commands
- Foreground and background process execution
- Job management
- Directory navigation
- File and directory management
- Process termination

### Deliverable 2

- CPU Scheduling Simulator
- Round Robin Scheduling
- Preemptive Priority Scheduling
- Scheduling metrics
- Simulated process management

### Deliverable 3

- Virtual memory management
- FIFO page replacement
- LRU page replacement
- Demand paging simulation
- Producer-Consumer synchronization
- Mutex and semaphore synchronization

### Deliverable 4

- Command piping
- Multiple command pipelines
- User authentication
- Administrator and standard user accounts
- Role-based file permissions
- Read, write, and execute access control
- Protected system files
- Secure shell integration

---

## Project Structure

```text
AdvancedShell_Deliverable4/
│
├── authentication.py
├── commands.py
├── jobs.py
├── memory_manager.py
├── permissions.py
├── piping.py
├── process_manager.py
├── scheduler.py
├── shell.py
├── synchronization.py
├── requirements.txt
├── users.json
├── file_permissions.json
├── TEST_COMMANDS.txt
│
├── test_files/
│   ├── admin_script.py
│   ├── application.log
│   ├── public.txt
│   └── system_config.txt
│
├── Deliverable 4 Screenshots/
│
└── README.md
```

---

## Requirements

- Python 3.10 or newer
- Windows 10/11

No third-party libraries are required for the core shell functionality.

---

## Running the Shell

From the project directory:

```bash
python shell.py
```

or

```bash
py shell.py
```

---

## Default User Accounts

### Administrator

```text
Username: admin
Password: Admin123!
```

Permissions:

- Read
- Write
- Execute

---

### Standard User

```text
Username: student
Password: Student123!
```

Permissions:

- Read protected files
- Read and write public files
- Cannot modify protected system files
- Cannot execute administrator-only scripts

---

## Example Commands

### Basic Commands

```text
pwd
ls
cd
mkdir Test
touch notes.txt
cat notes.txt
rm notes.txt
```

### Process Management

```text
jobs
kill <pid>
fg <job_id>
bg <job_id>
```

### CPU Scheduling

```text
addproc P1 6 1
addproc P2 4 2
schedule rr 2
metrics
```

### Memory Management

```text
memconfig 3 4 fifo
memalloc 101 5
memaccess 101 0
memaccess 101 1
memstat
memfree 101
```

### Synchronization

```text
producerconsumer
producerconsumer 2 2 5 3
syncstat
```

### Command Piping

```text
ls | grep py

cat test_files/application.log | grep error

cat test_files/application.log | grep error | sort | count
```

### Security

```text
whoami

permissions test_files/system_config.txt

permissions test_files/admin_script.py

write test_files/public.txt Sample update

runfile test_files/admin_script.py
```

---

## Testing

The project was tested using the following scenarios:

- Successful authentication using administrator and standard accounts
- Invalid login attempts
- Background and foreground process management
- CPU scheduling simulations
- Virtual memory allocation and page replacement
- Producer-consumer synchronization
- Single-stage command pipelines
- Multi-stage command pipelines
- Standard-user permission restrictions
- Administrator access to protected resources

---

## Screenshots Included

The accompanying report contains screenshots demonstrating:

- User authentication
- Command piping
- Multi-stage command pipelines
- Standard-user file permissions
- Access restriction enforcement
- Administrator authentication
- Administrator modification of protected files
- Administrator execution of protected scripts

---

## Learning Outcomes

This project demonstrates practical implementation of the following operating system concepts:

- Process Management
- Job Control
- CPU Scheduling
- Virtual Memory Management
- FIFO Page Replacement
- LRU Page Replacement
- Process Synchronization
- Mutexes and Semaphores
- Command Interpretation
- Command Piping
- User Authentication
- Role-Based Access Control
- File Permission Management
- Integrated Shell Design

---

## Author

**Nabiha Sadaf, Nasser Hasan Padilla, Samia Zaman & Tanmay Siwach**

**Course:** MSCS 630 – Advanced Operating Systems

**University of the Cumberlands**
