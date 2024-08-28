# Cyclone - A Distributed Task Driven Framework

A Distributed Task Driven Framework for Generic Task Execution on a Cluster

## Prerequisites

### Required

* **Python** - Standard Library
* **Python bindings for 0MQ (pyzmq)** - Interprocess communication between different components e.g. master, controller, etc.

### Optional

* **ClusterShell (clustershell)** - For RangeSet notation specifying Lustre OST indexes
* **LfsUtils (lfsutils)** - Utility library for accessing the Lustre filesystem
* **MySQL Connector Python (mysql)** - For storing task results into a MySQL database
* **HTTP library (requests)** - For communication with the Prometheus Pushgateway

## Versions

| Cyclone | Python | pyzmq  |
| :-----: | :----: | :----: |
| 2.0.5   | 3.9.12 | 22.3.0 |
| 2.0.2   | 3.8.5  | 20.0.0 |
| 2.0.0   | 3.6.0  | 19.0.0 |

## Architecture

![Architecture](Documentation/img/architecture.svg#left)

## Components

### Core

#### Master

#### Task Generator

#### Controller

#### Worker

### Optional

#### MySQL Database Proxy

#### Prometheus Pushgateway Client

## Features

### Load Balancing

Task distribution is done in a FCFS way. The fastest controller will get more tasks assigned to its worker than a controller that takes more time to process its assigned tasks.

### Scalability

During runtime new controller instances can be started even after the master is already running. Thus, not all instances must be started at the start and the number of instances must not be kept equal.

### Generic Task Interface

A specific task to be executed must implement the [BaseTask](task/base_task.py) interface.

### Distributed Task Execution

Tasks are executed by so called worker threads within a controller instance.

### Task Redispatching

If a task execution runs into a timeout, the proper task is redispatched.  

> This feature is currently not available and needs to be updated ([see issue](https://github.com/GSI-HPC/cyclone-distributed-task-driven-framework/issues/15)).

## Supported Tasks

* Benchmarking
* [Lustre OST Migration](Documentation/lustre_ost_migration.md)
* Lustre OST Monitoring
* Lustre File Creation Check

## How to Create a Task

1. Create a specific task class that inherites from `BaseTask` and implements the `execute` method.
2. The constructor of the new task class must contain each property that should be serialized to the controller instances.
3. A XML task file can be used to preinitalize the class properties.

> Check the LustreOstMigrateTask class for an example implementation.

## Slides

* [Introduction as Task Driven Framework for Lustre Monitoring](Slides/2017_10_04-task_driven_framework_for_lustre_monitoring.pdf)
* [File Migration on Lustre](Slides/2024_02_22-lustre_file_migration.pdf)
