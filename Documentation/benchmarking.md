# Benchmarking

A benchmarking test is implemented for Cyclone that processes a complete communication cycle  
between the master and controller with given number of worker.  

It can also be considered as an scalability test for the application,  
how many messages can be processed for a given time period.

A benchmark task does simulate a very small load by doing a sleep between 0 to 100ms.

To drop the wait time and get a more precise result for the message communication this [issue](https://github.com/GSI-HPC/cyclone-distributed-task-driven-framework/issues/26) should be considered.

> The benchmarking can also be used for testing the communication protocoll within Cyclone.

## Configuration

### Task Generator

[Example config file for the task generator](../Configuration/benchmark_task_generator.conf)

#### Section: control

| Name           | Type   | Value  | Description                                             |
| -------------- | ------ | ------ | ------------------------------------------------------- |
| num\_tasks     | Number | 1-100M | Number of tasks to be processed                         |
| poll\_time\_ms | Number | 1-1000 | Time for the task generator to check for finished tasks |

