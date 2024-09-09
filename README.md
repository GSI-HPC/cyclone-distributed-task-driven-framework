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

The master component is the central unit of Cyclone where controller can register.  
It is responsible for managing and scheduling tasks to controller.

##### Task Generator

The task generator is an interface which is attached to the master.  

Before dispatching new tasks to controller a specific task generator must be implemented,  
which provides tasks to the master.

#### Controller

A controller communicates with the master to receive new tasks to be executed.  

The controller itself delegates tasks to the attached worker.  
It also manages how many workers are available for task execution.

##### Worker

A worker executes a task that it received by the proper controller instance.

### Optional

#### MySQL Database Proxy

The MySQL database proxy acts like a client to a proper DBMS.  

It buffers e.g. monitoring metric values it receives from task results and saves them bulk-wise to the proper MySQL database.  

Otherwise each worker would have to send its task result to the MySQL instance each time.

> As an example how the MySQL database proxy is used, refer to the [Lustre OST monitoring](Documentation/lustre_ost_monitoring.md) use case.

#### Prometheus Pushgateway Client

The Prometheus pushgateway client is used to send monitoring metrics to the Promentheus monitoring system.

> See the monitoring use case for the [Lustre file creation check](Documentation/lustre_file_creation_check.md) for an example.

## Features

### Load Balancing

Task distribution is done in a FCFS way. The fastest controller will get more tasks assigned to its worker than a controller that takes more time to process its assigned tasks.

### Scalability

During runtime new controller instances can be started even after the master is already running. Thus, not all instances must be started at the start and the number of instances must not be kept equal.

### Generic Task Interface

A specific task to be executed must implement the [BaseTask](task/base_task.py) interface.

### Distributed Task Execution

Tasks are executed by so called worker within a controller instance.

### Task Redispatching

If a task execution runs into a timeout, the proper task is redispatched.  

> This feature is currently not available and needs to be updated (see [issue](https://github.com/GSI-HPC/cyclone-distributed-task-driven-framework/issues/15)).

## Supported Use Cases

* [Benchmarking](Documentation/benchmarking.md)
* [Lustre OST Migration](Documentation/lustre_ost_migration.md)
* [Lustre OST Monitoring](Documentation/lustre_ost_monitoring.md)
* [Lustre File Creation Check](Documentation/lustre_file_creation_check.md)

## Controlling Cyclone

### Master

#### Configuration

[Example master config file](Configuration/master.conf)

##### Section: control

| Name                       | Type   | Value | Description                                                    |
| -------------------------- | ------ | ----- | -------------------------------------------------------------- |
| pid\_file                  | String | Path  | Path to pid file for running just one master process           |
| controller\_timeout        | Number | n>=0  | Timeout in seconds waiting for an expected controller response |
| controller\_wait\_duration | Number | n>=0  | Wait time in seconds for controller if no tasks are available  |
| task\_resend\_timeout      | Number | n>=0  | Time duration before resending a task                          |

##### Section: comm

| Name                       | Type   | Value        | Description                                                 |
| -------------------------- | ------ | ------------ | ----------------------------------------------------------- |
| target                     | String | \*           | Network target from which to accept messages '\*' means all |
| port                       | Number | 1024 - 65535 | TCP port for network communication with controller          |
| poll\_timeout              | Number | n>=0         | Polling timeout in seconds waiting for controller messages  |

##### Section: log

| Name                       | Type   | Value | Description                                                       |
| -------------------------- | ------ | ------| ----------------------------------------------------------------- |
| filename                   | String | Path  | Filepath for log file of master including specific task generator |

##### Section: task\_generator

This section describes the parameter how to specify a task generator to use.

| Name                       | Type   | Value  | Description                                                    |
| -------------------------- | ------ | ------ | -------------------------------------------------------------- |
| module                     | String | *      | Python module path to task generator                           |
| class                      | String | *      | Class name of task generator                                   |
| config\_file               | String | Path   | Filepath to config file of the specific task generator         |

#### Start

```bash
# Starts the master component with the attached task generator:  
./cyclone-master.py -f Configuration/master.conf
```

It is recommended to start the master component first and than the attaching controller.  
The master can also be started after the controller, but this might lead to timeouts if the controller do not find the master in time.

> Currently there is a PID control check for the executable name that avoids running multiple processes of the same program name on a host.
> To run multiple instances the executable names must be different.

#### Stop

Master can be stopped by sending a kill signal with the proper PID with `kill <PID>`.  

The PID can be retrieved in multiple ways e.g. from the log or from PID file:  

```bash
# Get PID from log file
grep "Master PID" Runtime/master.log

# Get PID from PID file
cat Runtime/master.pid
```

### Controller

#### Configuration

[Example controller config file](Configuration/controller.conf)

##### Section: control

| Name                           | Type   | Value | Description                                                    |
| ------------------------------ | ------ | ----- | -------------------------------------------------------------- |
| pid\_file                      | String | Path  | Path to pid file for running just one controller process       |
| request\_retry\_wait\_duration | Number | n>=0  | Seconds to wait until trying next request to master            |
| max\_num\_request\_retries     | Number | n>=0  | Max number of request attempts before quiting                  |

##### Section: comm

| Name                           | Type   | Value        | Description                                              |
| ------------------------------ | ------ | ------------ | -------------------------------------------------------- |
| target                         | String | IP-Addr      | IP address of master process                             |
| port                           | Number | 1024 - 65535 | TCP port for network communication with master           |
| poll\_timeout                  | Number | n>0          | Polling timeout for new messages                         |

##### Section: log

| Name                           | Type   | Value  | Description                                                    |
| ------------------------------ | ------ | ------ | -------------------------------------------------------------- |
| filename                       | String | Path   | Filepath of log file for controller                            |

##### Section: processing

| Name                           | Type   | Value | Description                                                    |
| ------------------------------ | ------ | ----- | -------------------------------------------------------------- |
| worker\_count                  | Number | n>0   | Number of worker processes available for task processing       |

#### Start

```bash
# Starts the controller:  
./cyclone-controller.py -f Configuration/controller.conf
```
It is recommendend to start the controller after the master.  
Otherwise the controller might run into a timeout if the master is not reachable.

> Currently there is a PID control check for the executable name that avoids running multiple processes of the same program name on a host.
> To run multiple instances the executable names must be different.

#### Stop

The controller will shutdown itself when receiving a stop signal by the master or when the master is not reachable.  

A controller can be send also a stop signal by the proper <PID> locally on a target host.  
The PID can be found e.g. in the proper log or PID file.

> In any case, if a controller gets killed or crashed this will result in an inconsistent state in Cyclone (see [issue](https://github.com/GSI-HPC/cyclone-distributed-task-driven-framework/issues/24)).

## How to Create a Task

1. Create a specific task class that inherites from `BaseTask` and implements the `execute` method.
2. The constructor of the new task class must contain each property that should be serialized to the controller instances.
3. A XML task file can be used to preinitalize the class properties.

## Slides

* [Introduction as Task Driven Framework for Lustre Monitoring (2017)](Slides/2017_10_04-task_driven_framework_for_lustre_monitoring.pdf)
* [File Migration on Lustre (2024)](Slides/2024_02_22-lustre_file_migration.pdf)
