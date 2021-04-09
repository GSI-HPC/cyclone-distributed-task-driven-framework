# Cyclone - A Distributed Task Driven Framework

A Distributed Task Driven Framework for Generic Task Execution on a Cluster.

## Requisites

### Required

**Python** - Standard Library
**Python bindings for 0MQ (pyzmq)** - Interprocess communication between master and controller.

### Optional

**MySQL Connector Python (mysql)** - For storing task results into a MySQL database.

## Versions

These versions have been successfully tested with the `BenchmarkTask` to check the core functioning of the framework.

| Cyclone | Python | pyzmq  |
| :-----: | :----: | :----: |
| 2.0.1   | 3.8.5  | 20.0.0 |
| 2.0.0   | 3.6.0  | 19.0.0 |

## Architecture

![Architecture](Documentation/img/architecture.svg#left)

## Components

* Master
* Task Generator
* Controller
* Worker

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

### Short Introduction Slides

Short introduction slides can be downloaded [here](https://www.eofs.eu/_media/events/lad17/05_gabriele_iannetti_task_driven_framework_for_lustre_monitoring.pdf) from the Lustre Administrators and Developers Workshop (LAD) 2017.

