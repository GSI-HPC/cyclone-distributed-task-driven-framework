# Cyclone - A Distributed Task Driven Framework

A Distributed Task Driven Framework for Generic Task Execution on a Cluster.

## Prerequisites

### Required

* **Python** - Standard Library
* **Python bindings for 0MQ (pyzmq)** - Interprocess communication between master, controller.

### Optional

* **YAML parser and emitter for Python (PyYAML)** - Parsing stripe information from Lustre.
* **MySQL Connector Python (mysql)** - For storing task results into a MySQL database.

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

* Master with attached Task Generator
* Controller
* Worker

### Optional

* MySQL Database Proxy
* Prometheus Pushgateway Client

## Features

* Fault Tolerance
* Load Balancing
* Scalability
* Generic Task Interface
* Distributed Task Execution
* Task Redispatching

### Supported Tasks

* Benchmarking
* [Lustre OST Migration](Documentation/lustre_ost_migration.md)
* Lustre OST Monitoring

### How to Create a Task

1. Create a specific task class that inherites from `BaseTask` and implements the `execute` method.
2. The constructor of the new task class must contain each property that should be serialized to the controller instances.
3. A XML task file can be used to preinitalize the class properties.

> Check the LustreOstMigrateTask class for an example implementation.

### Short Introduction Slides

Short introduction slides can be downloaded [here](https://www.eofs.eu/_media/events/lad17/05_gabriele_iannetti_task_driven_framework_for_lustre_monitoring.pdf) from the Lustre Administrators and Developers Workshop (LAD) 2017.

